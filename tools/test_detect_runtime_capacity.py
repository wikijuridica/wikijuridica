#!/usr/bin/env python3

import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "detect-runtime-capacity"


class RuntimeCapacityTest(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.base = Path(self.tempdir.name)
        self.proc = self.base / "proc"
        self.sys = self.base / "sys"
        self.cgroup = self.base / "cgroup"
        (self.proc / "self").mkdir(parents=True)
        (self.sys / "devices/system/cpu").mkdir(parents=True)
        self.cgroup.mkdir()

    def tearDown(self):
        self.tempdir.cleanup()

    def write(self, path: Path, payload: str):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(payload, encoding="utf-8")

    def set_cpu_inputs(self, online: str, allowed: str, load1: str = "0.00"):
        self.write(self.sys / "devices/system/cpu/online", online + "\n")
        self.write(
            self.proc / "self/status",
            "Name:\ttest\nCpus_allowed_list:\t" + allowed + "\n",
        )
        self.write(self.proc / "loadavg", f"{load1} 0.00 0.00 1/1 1\n")

    def run_tool(self, *args, env=None, timeout=3):
        command = [
            str(TOOL),
            "--proc-root",
            str(self.proc),
            "--sys-root",
            str(self.sys),
            "--cgroup-root",
            str(self.cgroup),
            *args,
        ]
        clean_env = os.environ.copy()
        for name in (
            "WIKI_RUNTIME_CAPACITY_MODE",
            "WIKI_RUNTIME_CAPACITY_OVERRIDE",
            "WIKI_RUNTIME_CAPACITY_CONSERVATIVE_RATIO",
        ):
            clean_env.pop(name, None)
        if env:
            clean_env.update(env)
        return subprocess.run(
            command,
            text=True,
            capture_output=True,
            env=clean_env,
            timeout=timeout,
        )

    def run_json(self, *args, env=None):
        result = self.run_tool("--format", "json", *args, env=env)
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(result.stdout)

    def run_json_unavailable(self, *args, env=None):
        result = self.run_tool("--format", "json", *args, env=env)
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertEqual(result.stderr, "")
        evidence = json.loads(result.stdout)
        self.assertEqual(evidence["status"], "unavailable_fail_closed")
        self.assertEqual(evidence["selection_source"], "unavailable_fail_closed")
        self.assertIsNone(evidence["selected_cpu_workers"])
        return evidence

    def configure_v2(self, membership="/team/job"):
        self.write(self.proc / "self/cgroup", f"0::{membership}\n")
        self.write(self.cgroup / "cgroup.controllers", "cpuset cpu\n")
        self.write(self.cgroup / "cpuset.cpus.effective", "0-15\n")
        self.write(self.cgroup / "team/cpuset.cpus.effective", "2-9\n")
        self.write(self.cgroup / "team/cpu.max", "350000 100000\n")
        self.write(self.cgroup / "team/job/cpu.max", "max 100000\n")

    def configure_unlimited_v2(self, cpus="0-7"):
        self.write(self.proc / "self/cgroup", "0::/\n")
        self.write(self.cgroup / "cgroup.controllers", "cpuset cpu\n")
        self.write(self.cgroup / "cpuset.cpus.effective", cpus + "\n")
        self.write(self.cgroup / "cpu.max", "max 100000\n")

    def test_v2_uses_affinity_cpuset_and_smallest_ancestor_quota(self):
        self.set_cpu_inputs("0-15", "0-11")
        self.configure_v2()
        evidence = self.run_json()
        self.assertEqual(evidence["cgroup_version"], "v2")
        self.assertEqual(evidence["online_cpu_count"], 16)
        self.assertEqual(evidence["affinity_cpu_count"], 12)
        self.assertEqual(evidence["cpuset_cpu_count"], 8)
        self.assertEqual(evidence["allowed_cpu_count"], 8)
        self.assertEqual(evidence["quota_cpu_capacity"], 3.5)
        self.assertEqual(evidence["effective_cpu_capacity"], 3.5)
        self.assertEqual(evidence["effective_worker_ceiling"], 4)
        self.assertEqual(evidence["selected_cpu_workers"], 4)
        self.assertEqual(evidence["errors"], [])

    def test_load_is_normalized_to_effective_capacity_and_reserves_busy_workers(self):
        self.set_cpu_inputs("0-15", "0-11", load1="8.0")
        self.configure_v2()
        evidence = self.run_json()
        self.assertEqual(evidence["normalized_load_cpu"], 1.75)
        self.assertEqual(evidence["busy_worker_estimate"], 2)
        self.assertEqual(evidence["selected_cpu_workers"], 2)
        self.assertGreater(evidence["headroom_cpu"], 1.7)

    def test_conservative_mode_is_proportional_without_fixed_ceiling(self):
        self.set_cpu_inputs("0-63", "0-63")
        self.write(self.proc / "self/cgroup", "0::/wide\n")
        self.write(self.cgroup / "cgroup.controllers", "cpuset cpu\n")
        self.write(self.cgroup / "wide/cpuset.cpus.effective", "0-63\n")
        self.write(self.cgroup / "wide/cpu.max", "max 100000\n")
        evidence = self.run_json("--mode", "conservative")
        self.assertEqual(evidence["effective_worker_ceiling"], 64)
        self.assertEqual(evidence["selected_cpu_workers"], 32)
        self.assertEqual(
            evidence["selection_source"],
            "live_headroom_conservative_proportional",
        )

    def test_explicit_override_has_no_arbitrary_cap_and_is_validated(self):
        self.set_cpu_inputs("0-3", "0-3")
        self.write(self.proc / "self/cgroup", "")
        evidence = self.run_json("--override", "97")
        self.assertEqual(evidence["selected_cpu_workers"], 97)
        self.assertEqual(evidence["selection_source"], "explicit_override")
        for bad in ("0", "-1", "4.5", "invalid"):
            result = self.run_tool("--override", bad)
            self.assertEqual(result.returncode, 2, (bad, result.stderr))

    def test_environment_override_and_ratio_are_explicit_inputs(self):
        self.set_cpu_inputs("0-7", "0-7")
        self.configure_unlimited_v2()
        evidence = self.run_json(
            env={"WIKI_RUNTIME_CAPACITY_OVERRIDE": "19"}
        )
        self.assertEqual(evidence["selected_cpu_workers"], 19)
        evidence = self.run_json(
            env={
                "WIKI_RUNTIME_CAPACITY_MODE": "conservative",
                "WIKI_RUNTIME_CAPACITY_CONSERVATIVE_RATIO": "0.75",
            }
        )
        self.assertEqual(evidence["selected_cpu_workers"], 6)

    def test_v1_uses_separate_cpu_and_cpuset_mounts_and_parent_quota(self):
        self.set_cpu_inputs("0-7", "0-7")
        cpu_mount = self.cgroup / "cpu"
        cpuset_mount = self.cgroup / "cpuset"
        self.write(
            self.proc / "self/mountinfo",
            "31 20 0:28 / "
            + str(cpu_mount)
            + " rw - cgroup cgroup rw,cpu,cpuacct\n"
            + "32 20 0:29 / "
            + str(cpuset_mount)
            + " rw - cgroup cgroup rw,cpuset\n",
        )
        self.write(
            self.proc / "self/cgroup",
            "2:cpu,cpuacct:/tenant/job\n3:cpuset:/tenant/job\n",
        )
        self.write(cpu_mount / "tenant/cpu.cfs_quota_us", "250000\n")
        self.write(cpu_mount / "tenant/cpu.cfs_period_us", "100000\n")
        self.write(cpu_mount / "tenant/job/cpu.cfs_quota_us", "-1\n")
        self.write(cpu_mount / "tenant/job/cpu.cfs_period_us", "100000\n")
        self.write(cpuset_mount / "tenant/job/cpuset.effective_cpus", "4-7\n")
        evidence = self.run_json()
        self.assertEqual(evidence["cgroup_version"], "v1")
        self.assertEqual(evidence["cpuset_cpu_count"], 4)
        self.assertEqual(evidence["quota_cpu_capacity"], 2.5)
        self.assertEqual(evidence["selected_cpu_workers"], 3)

    def test_v2_selects_mount_whose_root_contains_membership(self):
        self.set_cpu_inputs("0-7", "0-7")
        unrelated = self.base / "unrelated-cgroup"
        unrelated.mkdir()
        self.write(
            self.proc / "self/mountinfo",
            "31 20 0:28 /other "
            + str(unrelated)
            + " rw - cgroup2 cgroup rw\n"
            + "32 20 0:29 /team "
            + str(self.cgroup)
            + " rw - cgroup2 cgroup rw\n",
        )
        self.write(self.proc / "self/cgroup", "0::/team/job\n")
        self.write(self.cgroup / "job/cpuset.cpus.effective", "0-5\n")
        self.write(self.cgroup / "job/cpu.max", "250000 100000\n")
        evidence = self.run_json()
        self.assertEqual(evidence["cpuset_cpu_count"], 6)
        self.assertEqual(evidence["quota_cpu_capacity"], 2.5)
        self.assertEqual(evidence["selected_cpu_workers"], 3)

    def test_missing_or_malformed_observation_is_unavailable(self):
        evidence = self.run_json_unavailable()
        self.assertTrue(evidence["errors"])

        self.set_cpu_inputs("not-a-list", "also-bad", load1="nan")
        evidence = self.run_json_unavailable()
        self.assertIn("load1_invalid", evidence["errors"])

    def test_malformed_cgroup_constraint_is_unavailable(self):
        self.set_cpu_inputs("0-7", "0-7")
        self.write(self.proc / "self/cgroup", "0::/job\n")
        self.write(self.cgroup / "cgroup.controllers", "cpuset cpu\n")
        self.write(self.cgroup / "job/cpuset.cpus.effective", "0-7\n")
        self.write(self.cgroup / "job/cpu.max", "broken quota\n")
        evidence = self.run_json_unavailable()
        self.assertIn("cgroup_v2_cpu_max_invalid", evidence["errors"])

    def test_malformed_or_unresolvable_cgroup_membership_is_unavailable(self):
        self.set_cpu_inputs("0-7", "0-7")
        self.write(self.proc / "self/cgroup", "malformed\n")
        evidence = self.run_json_unavailable()
        self.assertIn("cgroup_membership_invalid", evidence["errors"])

        self.write(self.proc / "self/cgroup", "0::/missing\n")
        self.write(self.cgroup / "cgroup.controllers", "cpuset cpu\n")
        evidence = self.run_json_unavailable()
        self.assertIn("cgroup_v2_membership_path_unavailable", evidence["errors"])

    def test_saturated_headroom_keeps_fail_safe_progress_of_one(self):
        self.set_cpu_inputs("0-7", "0-7", load1="64")
        self.configure_unlimited_v2()
        evidence = self.run_json()
        self.assertEqual(evidence["selected_cpu_workers"], 1)
        self.assertTrue(evidence["headroom_saturated"])

    def test_integer_interface_is_parseable_and_emits_json_evidence(self):
        self.set_cpu_inputs("0-7", "0-7", load1="1.1")
        self.configure_unlimited_v2()
        result = self.run_tool()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertRegex(result.stdout, r"^[1-9][0-9]*\n$")
        prefix = "detect-runtime-capacity: evidence="
        self.assertTrue(result.stderr.startswith(prefix), result.stderr)
        evidence = json.loads(result.stderr[len(prefix) :])
        self.assertEqual(int(result.stdout), evidence["selected_cpu_workers"])
        self.assertEqual(evidence["probe_policy"], "one_shot_no_sleep_no_poll")
        self.assertEqual(
            evidence["go_runtime_policy"],
            "leave_GOMAXPROCS_unset_unless_explicit_override",
        )

    def test_missing_cgroup_evidence_cannot_be_consumed_as_one_worker(self):
        self.set_cpu_inputs("0-7", "0-7")
        evidence = self.run_json_unavailable()
        self.assertIn("cgroup_membership_unavailable", evidence["errors"])

        integer = self.run_tool()
        self.assertEqual(integer.returncode, 1)
        self.assertEqual(integer.stdout, "")
        prefix = "detect-runtime-capacity: evidence="
        self.assertTrue(integer.stderr.startswith(prefix), integer.stderr)
        integer_evidence = json.loads(integer.stderr[len(prefix) :])
        self.assertIsNone(integer_evidence["selected_cpu_workers"])

    def test_fifo_observation_is_rejected_without_blocking(self):
        self.set_cpu_inputs("0-7", "0-7")
        self.configure_unlimited_v2()
        online = self.sys / "devices/system/cpu/online"
        online.unlink()
        os.mkfifo(online)
        evidence = self.run_json_unavailable()
        self.assertIn("online_cpu_list_not_regular", evidence["errors"])

    def test_symlink_observation_is_not_followed(self):
        self.set_cpu_inputs("0-7", "0-7")
        self.configure_unlimited_v2()
        target = self.base / "untrusted-online"
        self.write(target, "0-7\n")
        online = self.sys / "devices/system/cpu/online"
        online.unlink()
        online.symlink_to(target)
        evidence = self.run_json_unavailable()
        self.assertIn("online_cpu_list_unreadable", evidence["errors"])

    def test_cgroup_directory_symlink_is_not_followed(self):
        self.set_cpu_inputs("0-7", "0-7")
        self.write(self.proc / "self/cgroup", "0::/job\n")
        self.write(self.cgroup / "cgroup.controllers", "cpuset cpu\n")
        outside = self.base / "outside-cgroup"
        self.write(outside / "cpuset.cpus.effective", "0-7\n")
        self.write(outside / "cpu.max", "max 100000\n")
        (self.cgroup / "job").symlink_to(outside, target_is_directory=True)
        evidence = self.run_json_unavailable()
        self.assertIn(
            "cgroup_v2_membership_path_unavailable",
            evidence["errors"],
        )

    def test_giant_cpu_interval_is_intersected_without_expansion(self):
        self.set_cpu_inputs("0-100000000", "0-7")
        self.configure_unlimited_v2()
        evidence = self.run_json()
        self.assertEqual(evidence["online_cpu_count"], 100000001)
        self.assertEqual(evidence["allowed_cpu_count"], 8)
        self.assertEqual(evidence["selected_cpu_workers"], 8)

    def test_huge_override_is_structured_configuration_error(self):
        result = self.run_tool("--format", "json", "--override", "9" * 5000)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(result.stderr, "")
        evidence = json.loads(result.stdout)
        self.assertEqual(evidence["status"], "configuration_error")
        self.assertEqual(evidence["errors"], ["configuration_error"])
        self.assertIsNone(evidence["selected_cpu_workers"])

    def test_probe_source_contains_no_sleep_or_poll_loop(self):
        source = TOOL.read_text(encoding="utf-8")
        self.assertNotIn("time.sleep", source)
        self.assertNotIn("from time import sleep", source)
        self.assertNotIn("cpus.update(range", source)
        self.assertIn("os.O_NOFOLLOW", source)
        self.assertIn("MAX_OBSERVATION_BYTES", source)
        self.assertIn('"probe_policy": "one_shot_no_sleep_no_poll"', source)


if __name__ == "__main__":
    unittest.main()
