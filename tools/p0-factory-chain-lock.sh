#!/bin/sh

p0_factory_chain_lock_fd_has_mode() {
	P0_FACTORY_CHAIN_LOCK_AUTH_FD="$1"
	P0_FACTORY_CHAIN_LOCK_AUTH_MODE="$2"
	[ -r "/proc/$$/fdinfo/$P0_FACTORY_CHAIN_LOCK_AUTH_FD" ] || return 1
	awk -v expected="$P0_FACTORY_CHAIN_LOCK_AUTH_MODE" '
		$1 == "lock:" && $3 == "FLOCK" && $4 == "ADVISORY" && $5 == expected {
			found = 1
		}
		END { exit(found ? 0 : 1) }
	' "/proc/$$/fdinfo/$P0_FACTORY_CHAIN_LOCK_AUTH_FD"
}

p0_factory_chain_lock_fd_is_authenticated() {
	P0_FACTORY_CHAIN_LOCK_AUTH_FD="$1"
	P0_FACTORY_CHAIN_LOCK_AUTH_PATH="$2"
	P0_FACTORY_CHAIN_LOCK_AUTH_MODE="$3"
	P0_FACTORY_CHAIN_LOCK_AUTH_FD_IDENTITY="$(stat -Lc '%d:%i' "/proc/$$/fd/$P0_FACTORY_CHAIN_LOCK_AUTH_FD" 2>/dev/null || true)"
	P0_FACTORY_CHAIN_LOCK_AUTH_PATH_IDENTITY="$(stat -Lc '%d:%i' "$P0_FACTORY_CHAIN_LOCK_AUTH_PATH" 2>/dev/null || true)"
	P0_FACTORY_CHAIN_LOCK_AUTH_FD_AUTHORITY="$(stat -Lc '%u:%a' "/proc/$$/fd/$P0_FACTORY_CHAIN_LOCK_AUTH_FD" 2>/dev/null || true)"
	[ -n "$P0_FACTORY_CHAIN_LOCK_AUTH_FD_IDENTITY" ] &&
		[ "$P0_FACTORY_CHAIN_LOCK_AUTH_FD_IDENTITY" = "$P0_FACTORY_CHAIN_LOCK_AUTH_PATH_IDENTITY" ] &&
		[ "$P0_FACTORY_CHAIN_LOCK_AUTH_FD_AUTHORITY" = "$(id -u):600" ] &&
		[ -f "/proc/$$/fd/$P0_FACTORY_CHAIN_LOCK_AUTH_FD" ] &&
		[ -f "$P0_FACTORY_CHAIN_LOCK_AUTH_PATH" ] &&
		[ ! -L "$P0_FACTORY_CHAIN_LOCK_AUTH_PATH" ] &&
		p0_factory_chain_lock_fd_has_mode "$P0_FACTORY_CHAIN_LOCK_AUTH_FD" "$P0_FACTORY_CHAIN_LOCK_AUTH_MODE"
}

p0_factory_chain_lock_acquire() {
	P0_FACTORY_CHAIN_LOCK_COMMAND="$1"
	shift || true
	P0_FACTORY_CHAIN_REPO_ROOT="${ROOT:-$(pwd)}"
	if ! command -v sha256sum >/dev/null 2>&1; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: sha256sum command is required for stable repository lock identity" >&2
		exit 75
	fi
	if ! P0_FACTORY_CHAIN_REPO_CANONICAL="$(CDPATH='' cd -- "$P0_FACTORY_CHAIN_REPO_ROOT" 2>/dev/null && pwd -P)" ||
		[ -z "$P0_FACTORY_CHAIN_REPO_CANONICAL" ]; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: cannot resolve canonical repository root: $P0_FACTORY_CHAIN_REPO_ROOT" >&2
		exit 75
	fi
	P0_FACTORY_CHAIN_REPO_IDENTITY="$(stat -Lc '%d:%i' "$P0_FACTORY_CHAIN_REPO_CANONICAL" 2>/dev/null || true)"
	case "$P0_FACTORY_CHAIN_REPO_IDENTITY" in
	'' | *[!0-9:]*)
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: cannot resolve repository device/inode identity: $P0_FACTORY_CHAIN_REPO_CANONICAL" >&2
		exit 75
		;;
	esac
	P0_FACTORY_CHAIN_LOCK_DOMAIN="${P0_FACTORY_CHAIN_LOCK_DOMAIN:-}"
	if [ -z "$P0_FACTORY_CHAIN_LOCK_DOMAIN" ]; then
		case "${WIKI_HEAVY_ARTIFACT_CLAIM_PATH:-}" in
		data/* | content/* | public/*)
			P0_FACTORY_CHAIN_LOCK_DOMAIN="artifact:${WIKI_HEAVY_ARTIFACT_CLAIM_PATH}"
			;;
		*)
			P0_FACTORY_CHAIN_LOCK_DOMAIN="${WIKI_HEAVY_LOCK_SCOPE:-legacy-shared-chain}"
			;;
		esac
	fi
	case "$P0_FACTORY_CHAIN_LOCK_DOMAIN" in
	'' | *'
'*)
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: P0_FACTORY_CHAIN_LOCK_DOMAIN must be a nonempty single line" >&2
		exit 2
		;;
	esac
	if [ "${#P0_FACTORY_CHAIN_LOCK_DOMAIN}" -gt 1024 ]; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: P0_FACTORY_CHAIN_LOCK_DOMAIN exceeds 1024 bytes" >&2
		exit 2
	fi
	P0_FACTORY_CHAIN_REPO_BASE_KEY="$({
		printf 'device_inode=%s\n' "$P0_FACTORY_CHAIN_REPO_IDENTITY"
	} | sha256sum | awk 'NF {print $1; exit}')"
	P0_FACTORY_CHAIN_REPO_KEY="$({
		printf 'device_inode=%s\n' "$P0_FACTORY_CHAIN_REPO_IDENTITY"
		printf 'lock_domain=%s\n' "$P0_FACTORY_CHAIN_LOCK_DOMAIN"
	} | sha256sum | awk 'NF {print $1; exit}')"
	case "$P0_FACTORY_CHAIN_REPO_KEY" in
	*[!0-9a-f]* | '')
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: failed to derive stable repository lock key" >&2
		exit 75
		;;
	esac
	if [ "${#P0_FACTORY_CHAIN_REPO_KEY}" -ne 64 ]; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: invalid stable repository lock key length" >&2
		exit 75
	fi
	case "$P0_FACTORY_CHAIN_REPO_BASE_KEY" in
	*[!0-9a-f]* | '')
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: failed to derive repository coordination key" >&2
		exit 75
		;;
	esac
	if [ "${#P0_FACTORY_CHAIN_REPO_BASE_KEY}" -ne 64 ]; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: invalid repository coordination key length" >&2
		exit 75
	fi
	# /tmp is the host-wide rendezvous, never the caller's session-specific
	# TMPDIR. Device/inode makes aliases of the same live root converge; the
	# authenticated artifact/scope domain prevents unrelated factory fronts from
	# sharing one global lock.  The historical directory prefix remains stable
	# because older wrappers recognize it during metadata cleanup.
	P0_FACTORY_CHAIN_LOCK_DIR="/tmp/portaljuridico-p0-factory-chain-v2-$P0_FACTORY_CHAIN_REPO_KEY"
	P0_FACTORY_CHAIN_LOCK_PATH="$P0_FACTORY_CHAIN_LOCK_DIR/p0-factory-chain.lock"
	P0_FACTORY_CHAIN_LOCK_META_PATH="$P0_FACTORY_CHAIN_LOCK_DIR/p0-factory-chain.lock.meta"
	P0_FACTORY_CHAIN_COORDINATION_DIR="/tmp/portaljuridico-p0-factory-coordination-v1-$P0_FACTORY_CHAIN_REPO_BASE_KEY"
	P0_FACTORY_CHAIN_COORDINATION_PATH="$P0_FACTORY_CHAIN_COORDINATION_DIR/p0-factory-coordination.lock"
	if [ "$P0_FACTORY_CHAIN_LOCK_DOMAIN" = "bootstrap-chain" ]; then
		P0_FACTORY_CHAIN_COORDINATION_MODE="exclusive"
	else
		P0_FACTORY_CHAIN_COORDINATION_MODE="shared"
	fi
	P0_FACTORY_CHAIN_REPO_ROOT="$P0_FACTORY_CHAIN_REPO_CANONICAL"
	P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS="${P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS:-0}"
	P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS="${P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS:-30}"
	export P0_FACTORY_CHAIN_LOCK_PATH
	export P0_FACTORY_CHAIN_LOCK_META_PATH
	export P0_FACTORY_CHAIN_LOCK_DOMAIN
	export P0_FACTORY_CHAIN_COORDINATION_PATH
	export P0_FACTORY_CHAIN_COORDINATION_MODE

	if ! command -v flock >/dev/null 2>&1; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: flock command is required for P0 factory chain lock" >&2
		exit 75
	fi

	if [ "${P0_FACTORY_CHAIN_LOCK_HELD:-}" = "1" ]; then
		P0_FACTORY_CHAIN_COORDINATION_REQUIRED_MODE="READ"
		if [ "$P0_FACTORY_CHAIN_COORDINATION_MODE" = "exclusive" ]; then
			P0_FACTORY_CHAIN_COORDINATION_REQUIRED_MODE="WRITE"
		fi
		if p0_factory_chain_lock_fd_is_authenticated 7 "$P0_FACTORY_CHAIN_COORDINATION_PATH" "$P0_FACTORY_CHAIN_COORDINATION_REQUIRED_MODE" &&
			p0_factory_chain_lock_fd_is_authenticated 8 "$P0_FACTORY_CHAIN_LOCK_PATH" "WRITE"; then
			return 0
		fi
		P0_FACTORY_CHAIN_COORDINATION_FD_IDENTITY="$(stat -Lc '%d:%i' "/proc/$$/fd/7" 2>/dev/null || true)"
		P0_FACTORY_CHAIN_LOCK_FD_IDENTITY="$(stat -Lc '%d:%i' "/proc/$$/fd/8" 2>/dev/null || true)"
		if [ -n "$P0_FACTORY_CHAIN_COORDINATION_FD_IDENTITY" ] || [ -n "$P0_FACTORY_CHAIN_LOCK_FD_IDENTITY" ]; then
			echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: inherited fd 7/8 lacks the required kernel lock, authority, repository or factory domain; refusing to replace it" >&2
			exit 75
		fi
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: ignored stale P0_FACTORY_CHAIN_LOCK_HELD without matching locked fd 7/8" >&2
		unset P0_FACTORY_CHAIN_LOCK_HELD
	fi

	P0_FACTORY_CHAIN_LOCK_TIMINGS=0
	for P0_FACTORY_CHAIN_LOCK_ARG in "$@"; do
		case "$P0_FACTORY_CHAIN_LOCK_ARG" in
		--timings)
			P0_FACTORY_CHAIN_LOCK_TIMINGS=1
			;;
		esac
	done

	case "$P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS" in
	'' | *[!0-9]*)
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS must be numeric seconds" >&2
		exit 2
		;;
	esac
	case "$P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS" in
	'' | *[!0-9]*)
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: P0_FACTORY_CHAIN_LOCK_WAIT_NOTICE_SECONDS must be numeric seconds" >&2
		exit 2
		;;
	esac
	if [ "$P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS" -gt 300 ]; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS must not exceed 300 seconds" >&2
		exit 2
	fi
	if [ -L "$P0_FACTORY_CHAIN_COORDINATION_DIR" ]; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: repository coordination directory cannot be a symlink: $P0_FACTORY_CHAIN_COORDINATION_DIR" >&2
		exit 75
	fi
	if ! mkdir -p "$P0_FACTORY_CHAIN_COORDINATION_DIR" ||
		[ -L "$P0_FACTORY_CHAIN_COORDINATION_DIR" ] ||
		[ ! -d "$P0_FACTORY_CHAIN_COORDINATION_DIR" ] ||
		! chmod 0700 "$P0_FACTORY_CHAIN_COORDINATION_DIR"; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: cannot create private repository coordination directory: $P0_FACTORY_CHAIN_COORDINATION_DIR" >&2
		exit 75
	fi
	P0_FACTORY_CHAIN_COORDINATION_DIR_AUTHORITY="$(stat -Lc '%u:%a' "$P0_FACTORY_CHAIN_COORDINATION_DIR" 2>/dev/null || true)"
	if [ "$P0_FACTORY_CHAIN_COORDINATION_DIR_AUTHORITY" != "$(id -u):700" ]; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: private repository coordination directory has wrong owner/mode/type: $P0_FACTORY_CHAIN_COORDINATION_DIR" >&2
		exit 75
	fi
	if [ -L "$P0_FACTORY_CHAIN_COORDINATION_PATH" ] ||
		{ [ -e "$P0_FACTORY_CHAIN_COORDINATION_PATH" ] && [ ! -f "$P0_FACTORY_CHAIN_COORDINATION_PATH" ]; }; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: repository coordination lock must be a regular non-symlink file: $P0_FACTORY_CHAIN_COORDINATION_PATH" >&2
		exit 75
	fi
	if [ -L "$P0_FACTORY_CHAIN_LOCK_DIR" ]; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: stable repository lock directory cannot be a symlink: $P0_FACTORY_CHAIN_LOCK_DIR" >&2
		exit 75
	fi
	if ! mkdir -p "$P0_FACTORY_CHAIN_LOCK_DIR" ||
		[ -L "$P0_FACTORY_CHAIN_LOCK_DIR" ] ||
		[ ! -d "$P0_FACTORY_CHAIN_LOCK_DIR" ] ||
		! chmod 0700 "$P0_FACTORY_CHAIN_LOCK_DIR"; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: cannot create private stable repository lock directory: $P0_FACTORY_CHAIN_LOCK_DIR" >&2
		exit 75
	fi
	P0_FACTORY_CHAIN_LOCK_DIR_AUTHORITY="$(stat -Lc '%u:%a' "$P0_FACTORY_CHAIN_LOCK_DIR" 2>/dev/null || true)"
	if [ "$P0_FACTORY_CHAIN_LOCK_DIR_AUTHORITY" != "$(id -u):700" ]; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: private lock directory has wrong owner/mode/type: $P0_FACTORY_CHAIN_LOCK_DIR" >&2
		exit 75
	fi
	if [ -L "$P0_FACTORY_CHAIN_LOCK_PATH" ] ||
		{ [ -e "$P0_FACTORY_CHAIN_LOCK_PATH" ] && [ ! -f "$P0_FACTORY_CHAIN_LOCK_PATH" ]; }; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: stable repository lock must be a regular non-symlink file: $P0_FACTORY_CHAIN_LOCK_PATH" >&2
		exit 75
	fi
	if [ -L "$P0_FACTORY_CHAIN_LOCK_META_PATH" ] ||
		{ [ -e "$P0_FACTORY_CHAIN_LOCK_META_PATH" ] && [ ! -f "$P0_FACTORY_CHAIN_LOCK_META_PATH" ]; }; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: stable repository lock metadata must be a regular non-symlink file: $P0_FACTORY_CHAIN_LOCK_META_PATH" >&2
		exit 75
	fi
	if [ -e "/proc/$$/fd/7" ] || [ -e "/proc/$$/fd/8" ]; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: fd 7/8 already open without authenticated inheritance; refusing to clobber caller descriptors" >&2
		exit 75
	fi
	# The repository gate is shared by independent artifact writers and
	# exclusive for the all-artifact bootstrap snapshot.  The domain lock then
	# serializes only writers that claim the same artifact/scope.  Acquiring in
	# this fixed order prevents deadlock while preserving useful parallelism.
	exec 7>>"$P0_FACTORY_CHAIN_COORDINATION_PATH"
	if ! chmod 0600 "$P0_FACTORY_CHAIN_COORDINATION_PATH" || [ -L "$P0_FACTORY_CHAIN_COORDINATION_PATH" ]; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: cannot authenticate opened repository coordination lock: $P0_FACTORY_CHAIN_COORDINATION_PATH" >&2
		exec 7>&-
		exit 75
	fi
	P0_FACTORY_CHAIN_COORDINATION_OPEN_IDENTITY="$(stat -Lc '%d:%i' "/proc/$$/fd/7" 2>/dev/null || true)"
	P0_FACTORY_CHAIN_COORDINATION_NAMED_IDENTITY="$(stat -Lc '%d:%i' "$P0_FACTORY_CHAIN_COORDINATION_PATH" 2>/dev/null || true)"
	P0_FACTORY_CHAIN_COORDINATION_OPEN_AUTHORITY="$(stat -Lc '%u:%a' "/proc/$$/fd/7" 2>/dev/null || true)"
	if [ -z "$P0_FACTORY_CHAIN_COORDINATION_OPEN_IDENTITY" ] ||
		[ "$P0_FACTORY_CHAIN_COORDINATION_OPEN_IDENTITY" != "$P0_FACTORY_CHAIN_COORDINATION_NAMED_IDENTITY" ] ||
		[ "$P0_FACTORY_CHAIN_COORDINATION_OPEN_AUTHORITY" != "$(id -u):600" ] ||
		[ ! -f "/proc/$$/fd/7" ]; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: opened repository coordination lock identity/path/mode mismatch: $P0_FACTORY_CHAIN_COORDINATION_PATH" >&2
		exec 7>&-
		exit 75
	fi
	if [ "$P0_FACTORY_CHAIN_COORDINATION_MODE" = "exclusive" ]; then
		if ! flock -n -x 7; then
			if [ "$P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS" -eq 0 ]; then
				echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: repository coordination gate busy; passive wait disabled mode=exclusive coordination_path=$P0_FACTORY_CHAIN_COORDINATION_PATH" >&2
				exit 75
			fi
			if ! flock -w "$P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS" -x 7; then
				echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: repository coordination gate blocked after ${P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS}s mode=exclusive coordination_path=$P0_FACTORY_CHAIN_COORDINATION_PATH" >&2
				exit 75
			fi
		fi
	else
		if ! flock -n -s 7; then
			if [ "$P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS" -eq 0 ]; then
				echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: repository coordination gate busy; passive wait disabled mode=shared coordination_path=$P0_FACTORY_CHAIN_COORDINATION_PATH" >&2
				exit 75
			fi
			if ! flock -w "$P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS" -s 7; then
				echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: repository coordination gate blocked after ${P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS}s mode=shared coordination_path=$P0_FACTORY_CHAIN_COORDINATION_PATH" >&2
				exit 75
			fi
		fi
	fi
	P0_FACTORY_CHAIN_COORDINATION_REQUIRED_MODE="READ"
	if [ "$P0_FACTORY_CHAIN_COORDINATION_MODE" = "exclusive" ]; then
		P0_FACTORY_CHAIN_COORDINATION_REQUIRED_MODE="WRITE"
	fi
	if ! p0_factory_chain_lock_fd_is_authenticated 7 "$P0_FACTORY_CHAIN_COORDINATION_PATH" "$P0_FACTORY_CHAIN_COORDINATION_REQUIRED_MODE"; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: acquired repository coordination fd 7 failed post-lock identity/mode authentication" >&2
		exit 75
	fi
	exec 8>>"$P0_FACTORY_CHAIN_LOCK_PATH"
	if ! chmod 0600 "$P0_FACTORY_CHAIN_LOCK_PATH" || [ -L "$P0_FACTORY_CHAIN_LOCK_PATH" ]; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: cannot authenticate opened factory-chain lock: $P0_FACTORY_CHAIN_LOCK_PATH" >&2
		exec 8>&-
		exit 75
	fi
	P0_FACTORY_CHAIN_LOCK_OPEN_IDENTITY="$(stat -Lc '%d:%i' "/proc/$$/fd/8" 2>/dev/null || true)"
	P0_FACTORY_CHAIN_LOCK_NAMED_IDENTITY="$(stat -Lc '%d:%i' "$P0_FACTORY_CHAIN_LOCK_PATH" 2>/dev/null || true)"
	P0_FACTORY_CHAIN_LOCK_OPEN_AUTHORITY="$(stat -Lc '%u:%a' "/proc/$$/fd/8" 2>/dev/null || true)"
	if [ -z "$P0_FACTORY_CHAIN_LOCK_OPEN_IDENTITY" ] ||
		[ "$P0_FACTORY_CHAIN_LOCK_OPEN_IDENTITY" != "$P0_FACTORY_CHAIN_LOCK_NAMED_IDENTITY" ] ||
		[ "$P0_FACTORY_CHAIN_LOCK_OPEN_AUTHORITY" != "$(id -u):600" ] ||
		[ ! -f "/proc/$$/fd/8" ]; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: opened factory-chain lock identity/path/mode mismatch: $P0_FACTORY_CHAIN_LOCK_PATH" >&2
		exec 8>&-
		exit 75
	fi
	P0_FACTORY_CHAIN_LOCK_START_EPOCH="$(date +%s 2>/dev/null || printf '0')"
	if [ "$P0_FACTORY_CHAIN_LOCK_TIMINGS" = "1" ]; then
		P0_FACTORY_CHAIN_LOCK_OWNER_META="$(p0_factory_chain_lock_owner_meta)"
		echo "TIMING $P0_FACTORY_CHAIN_LOCK_COMMAND wrapper_event=waiting_for_factory_chain_lock lock_path=$P0_FACTORY_CHAIN_LOCK_PATH meta_path=$P0_FACTORY_CHAIN_LOCK_META_PATH wait_limit_s=$P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS owner_meta=$P0_FACTORY_CHAIN_LOCK_OWNER_META" >&2
	fi

	if ! flock -n 8; then
		p0_factory_chain_lock_active_analysis 0 "reorient_to_non_conflicting_front_or_use_explicit_bounded_wait"
		if [ "$P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS" -eq 0 ]; then
			echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: factory chain lock busy; passive wait disabled lock_path=$P0_FACTORY_CHAIN_LOCK_PATH" >&2
			exit 75
		fi
		if ! flock -w "$P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS" 8; then
			p0_factory_chain_lock_active_analysis "$P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS" "bounded_wait_exhausted_reorient_to_independent_front"
			echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: factory chain lock blocked after ${P0_FACTORY_CHAIN_LOCK_WAIT_SECONDS}s lock_path=$P0_FACTORY_CHAIN_LOCK_PATH" >&2
			exit 75
		fi
	fi
	if ! p0_factory_chain_lock_fd_is_authenticated 8 "$P0_FACTORY_CHAIN_LOCK_PATH" "WRITE"; then
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: acquired factory-domain fd 8 failed post-lock identity/mode authentication" >&2
		exit 75
	fi

	if [ "$P0_FACTORY_CHAIN_LOCK_TIMINGS" = "1" ]; then
		P0_FACTORY_CHAIN_LOCK_NOW_EPOCH="$(date +%s 2>/dev/null || printf '0')"
		P0_FACTORY_CHAIN_LOCK_ELAPSED=0
		if [ "$P0_FACTORY_CHAIN_LOCK_START_EPOCH" -gt 0 ] && [ "$P0_FACTORY_CHAIN_LOCK_NOW_EPOCH" -gt 0 ]; then
			P0_FACTORY_CHAIN_LOCK_ELAPSED=$((P0_FACTORY_CHAIN_LOCK_NOW_EPOCH - P0_FACTORY_CHAIN_LOCK_START_EPOCH))
		fi
		p0_factory_chain_lock_write_meta "$P0_FACTORY_CHAIN_LOCK_NOW_EPOCH"
		echo "TIMING $P0_FACTORY_CHAIN_LOCK_COMMAND wrapper_event=factory_chain_lock_acquired elapsed_s=$P0_FACTORY_CHAIN_LOCK_ELAPSED lock_path=$P0_FACTORY_CHAIN_LOCK_PATH meta_path=$P0_FACTORY_CHAIN_LOCK_META_PATH" >&2
	else
		p0_factory_chain_lock_write_meta "$P0_FACTORY_CHAIN_LOCK_START_EPOCH"
	fi
	trap 'p0_factory_chain_lock_cleanup_owned_meta' EXIT
	trap 'p0_factory_chain_lock_signal_exit 129' HUP
	trap 'p0_factory_chain_lock_signal_exit 130' INT
	trap 'p0_factory_chain_lock_signal_exit 131' QUIT
	trap 'p0_factory_chain_lock_signal_exit 143' TERM
	export P0_FACTORY_CHAIN_LOCK_HELD=1
}

p0_factory_chain_lock_cleanup_owned_meta() {
	if [ -L "${P0_FACTORY_CHAIN_LOCK_META_PATH:-}" ]; then
		return 0
	fi
	P0_FACTORY_CHAIN_LOCK_META_OWNER="$(sed -n 's/^pid=//p' "${P0_FACTORY_CHAIN_LOCK_META_PATH:-}" 2>/dev/null | sed -n '1p')"
	if [ "$P0_FACTORY_CHAIN_LOCK_META_OWNER" = "$$" ]; then
		rm -f -- "$P0_FACTORY_CHAIN_LOCK_META_PATH" >/dev/null 2>&1 || true
	fi
}

p0_factory_chain_lock_signal_exit() {
	P0_FACTORY_CHAIN_LOCK_SIGNAL_STATUS="$1"
	trap - HUP INT QUIT TERM
	# This helper owns only the flock and its metadata.  Process-tree lifecycle
	# belongs to tools/supervise-process-tree (pidfd + subreapers); a shell
	# snapshot/kill loop here would be racy and could target recycled PIDs.
	p0_factory_chain_lock_cleanup_owned_meta
	trap - EXIT
	exit "$P0_FACTORY_CHAIN_LOCK_SIGNAL_STATUS"
}

p0_factory_chain_lock_owner_meta() {
	if [ -L "${P0_FACTORY_CHAIN_LOCK_META_PATH:-}" ] || [ ! -s "${P0_FACTORY_CHAIN_LOCK_META_PATH:-}" ]; then
		printf 'missing'
		return 0
	fi
	tr '\n' ';' <"$P0_FACTORY_CHAIN_LOCK_META_PATH" 2>/dev/null || printf 'unreadable'
}

p0_factory_chain_lock_meta_value() {
	P0_FACTORY_CHAIN_LOCK_META_KEY="$1"
	if [ -L "${P0_FACTORY_CHAIN_LOCK_META_PATH:-}" ] || [ ! -s "${P0_FACTORY_CHAIN_LOCK_META_PATH:-}" ]; then
		printf 'missing'
		return 0
	fi
	sed -n "s/^$P0_FACTORY_CHAIN_LOCK_META_KEY=//p" "$P0_FACTORY_CHAIN_LOCK_META_PATH" 2>/dev/null | sed -n '1p'
}

p0_factory_chain_lock_first_child_pid() {
	P0_FACTORY_CHAIN_LOCK_PARENT_PID="$1"
	case "$P0_FACTORY_CHAIN_LOCK_PARENT_PID" in
	'' | *[!0-9]*)
		return 1
		;;
	esac
	if ! command -v pgrep >/dev/null 2>&1; then
		return 1
	fi
	pgrep -P "$P0_FACTORY_CHAIN_LOCK_PARENT_PID" 2>/dev/null | sed -n '1p'
}

p0_factory_chain_lock_first_descendant_pid() {
	P0_FACTORY_CHAIN_LOCK_DESCENDANT_PARENT="$1"
	P0_FACTORY_CHAIN_LOCK_DESCENDANT_DEPTH=0
	P0_FACTORY_CHAIN_LOCK_DESCENDANT_FRONTIER="$P0_FACTORY_CHAIN_LOCK_DESCENDANT_PARENT"
	P0_FACTORY_CHAIN_LOCK_DESCENDANT_BEST=""
	while [ "$P0_FACTORY_CHAIN_LOCK_DESCENDANT_DEPTH" -lt 8 ]; do
		P0_FACTORY_CHAIN_LOCK_DESCENDANT_NEXT=""
		for P0_FACTORY_CHAIN_LOCK_DESCENDANT_NODE in $P0_FACTORY_CHAIN_LOCK_DESCENDANT_FRONTIER; do
			case "$P0_FACTORY_CHAIN_LOCK_DESCENDANT_NODE" in
			'' | *[!0-9]*)
				continue
				;;
			esac
			P0_FACTORY_CHAIN_LOCK_DESCENDANT_CHILDREN="$(pgrep -P "$P0_FACTORY_CHAIN_LOCK_DESCENDANT_NODE" 2>/dev/null || true)"
			for P0_FACTORY_CHAIN_LOCK_DESCENDANT_CHILD in $P0_FACTORY_CHAIN_LOCK_DESCENDANT_CHILDREN; do
				case "$P0_FACTORY_CHAIN_LOCK_DESCENDANT_CHILD" in
				'' | *[!0-9]*)
					continue
					;;
				esac
				P0_FACTORY_CHAIN_LOCK_DESCENDANT_NEXT="$P0_FACTORY_CHAIN_LOCK_DESCENDANT_NEXT $P0_FACTORY_CHAIN_LOCK_DESCENDANT_CHILD"
				P0_FACTORY_CHAIN_LOCK_DESCENDANT_COMMAND="$(p0_factory_chain_lock_pid_command "$P0_FACTORY_CHAIN_LOCK_DESCENDANT_CHILD")"
				case "$P0_FACTORY_CHAIN_LOCK_DESCENDANT_COMMAND" in
				'' | sleep | sleep\ * | *" sleep "*)
					continue
					;;
				esac
				P0_FACTORY_CHAIN_LOCK_DESCENDANT_BEST="$P0_FACTORY_CHAIN_LOCK_DESCENDANT_CHILD"
			done
		done
		if [ -z "$P0_FACTORY_CHAIN_LOCK_DESCENDANT_NEXT" ]; then
			break
		fi
		P0_FACTORY_CHAIN_LOCK_DESCENDANT_FRONTIER="$P0_FACTORY_CHAIN_LOCK_DESCENDANT_NEXT"
		P0_FACTORY_CHAIN_LOCK_DESCENDANT_DEPTH=$((P0_FACTORY_CHAIN_LOCK_DESCENDANT_DEPTH + 1))
	done
	if [ -n "$P0_FACTORY_CHAIN_LOCK_DESCENDANT_BEST" ]; then
		printf '%s' "$P0_FACTORY_CHAIN_LOCK_DESCENDANT_BEST"
		return 0
	fi
	return 1
}

p0_factory_chain_lock_pid_cpu() {
	P0_FACTORY_CHAIN_LOCK_CPU_PID="$1"
	if command -v ps >/dev/null 2>&1; then
		ps -p "$P0_FACTORY_CHAIN_LOCK_CPU_PID" -o %cpu= 2>/dev/null | sed -n '1p' | tr -d ' '
	fi
}

p0_factory_chain_lock_pid_command() {
	P0_FACTORY_CHAIN_LOCK_COMMAND_PID="$1"
	if command -v ps >/dev/null 2>&1; then
		ps -p "$P0_FACTORY_CHAIN_LOCK_COMMAND_PID" -o args= 2>/dev/null | sed -n '1p' | tr '\n' ' '
	fi
}

p0_factory_chain_lock_active_analysis() {
	P0_FACTORY_CHAIN_LOCK_ELAPSED_SECONDS="${1:-0}"
	P0_FACTORY_CHAIN_LOCK_NEXT_ACTION="${2:-inspect_active_command_before_waiting}"
	P0_FACTORY_CHAIN_LOCK_ACTIVE_OWNER_PID="$(p0_factory_chain_lock_meta_value pid)"
	P0_FACTORY_CHAIN_LOCK_OWNER_COMMAND="$(p0_factory_chain_lock_meta_value command)"
	P0_FACTORY_CHAIN_LOCK_OWNER_SCOPE="$(p0_factory_chain_lock_meta_value lock_scope)"
	P0_FACTORY_CHAIN_LOCK_OWNER_ARTIFACT="$(p0_factory_chain_lock_meta_value artifact_claim_path)"
	P0_FACTORY_CHAIN_LOCK_OWNER_THROUGHPUT_EXPECTED="$(p0_factory_chain_lock_meta_value throughput_expected)"
	P0_FACTORY_CHAIN_LOCK_OWNER_BUDGET="$(p0_factory_chain_lock_meta_value budget_ms)"
	P0_FACTORY_CHAIN_LOCK_OWNER_STOP_CONDITION="$(p0_factory_chain_lock_meta_value stop_condition)"
	P0_FACTORY_CHAIN_LOCK_CHILD_PID="$(p0_factory_chain_lock_meta_value child_pid)"
	P0_FACTORY_CHAIN_LOCK_CHILD_COMMAND="$(p0_factory_chain_lock_meta_value child_command)"
	case "$P0_FACTORY_CHAIN_LOCK_CHILD_PID" in
	'' | missing | *[!0-9]*)
		P0_FACTORY_CHAIN_LOCK_CHILD_PID="$(p0_factory_chain_lock_first_descendant_pid "$P0_FACTORY_CHAIN_LOCK_ACTIVE_OWNER_PID" || true)"
		;;
	esac
	case "$P0_FACTORY_CHAIN_LOCK_CHILD_PID" in
	'' | *[!0-9]*)
		P0_FACTORY_CHAIN_LOCK_CHILD_PID="missing"
		;;
	esac
	if [ "$P0_FACTORY_CHAIN_LOCK_CHILD_PID" != "missing" ]; then
		P0_FACTORY_CHAIN_LOCK_DISCOVERED_CHILD_COMMAND="$(p0_factory_chain_lock_pid_command "$P0_FACTORY_CHAIN_LOCK_CHILD_PID")"
		if [ -n "$P0_FACTORY_CHAIN_LOCK_DISCOVERED_CHILD_COMMAND" ]; then
			P0_FACTORY_CHAIN_LOCK_CHILD_COMMAND="$P0_FACTORY_CHAIN_LOCK_DISCOVERED_CHILD_COMMAND"
		fi
	fi
	if [ -z "$P0_FACTORY_CHAIN_LOCK_CHILD_COMMAND" ] || [ "$P0_FACTORY_CHAIN_LOCK_CHILD_COMMAND" = "missing" ]; then
		P0_FACTORY_CHAIN_LOCK_CHILD_COMMAND="missing"
	fi
	P0_FACTORY_CHAIN_LOCK_MONITORED_PID="$P0_FACTORY_CHAIN_LOCK_ACTIVE_OWNER_PID"
	if [ "$P0_FACTORY_CHAIN_LOCK_CHILD_PID" != "missing" ]; then
		P0_FACTORY_CHAIN_LOCK_MONITORED_PID="$P0_FACTORY_CHAIN_LOCK_CHILD_PID"
	fi
	P0_FACTORY_CHAIN_LOCK_OWNER_CPU="missing"
	if [ "$P0_FACTORY_CHAIN_LOCK_MONITORED_PID" != "missing" ] && [ -n "$P0_FACTORY_CHAIN_LOCK_MONITORED_PID" ]; then
		P0_FACTORY_CHAIN_LOCK_OWNER_CPU="$(p0_factory_chain_lock_pid_cpu "$P0_FACTORY_CHAIN_LOCK_MONITORED_PID")"
		if [ -z "$P0_FACTORY_CHAIN_LOCK_OWNER_CPU" ]; then
			P0_FACTORY_CHAIN_LOCK_OWNER_CPU="missing"
		fi
	fi
	if [ -z "$P0_FACTORY_CHAIN_LOCK_OWNER_ARTIFACT" ] || [ "$P0_FACTORY_CHAIN_LOCK_OWNER_ARTIFACT" = "missing" ]; then
		P0_FACTORY_CHAIN_LOCK_OWNER_ARTIFACT="${WIKI_HEAVY_ARTIFACT_CLAIM_PATH:-none}"
	fi
	P0_FACTORY_CHAIN_LOCK_ELAPSED_MS=$((P0_FACTORY_CHAIN_LOCK_ELAPSED_SECONDS * 1000))
	echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: analise_comando_ativo pid=$P0_FACTORY_CHAIN_LOCK_ACTIVE_OWNER_PID child_pid=$P0_FACTORY_CHAIN_LOCK_CHILD_PID comando=$P0_FACTORY_CHAIN_LOCK_OWNER_COMMAND child_command=$P0_FACTORY_CHAIN_LOCK_CHILD_COMMAND artefato=$P0_FACTORY_CHAIN_LOCK_OWNER_ARTIFACT lock_scope=$P0_FACTORY_CHAIN_LOCK_OWNER_SCOPE elapsed_ms=$P0_FACTORY_CHAIN_LOCK_ELAPSED_MS cpu_percent=$P0_FACTORY_CHAIN_LOCK_OWNER_CPU throughput=absent throughput_expected=$P0_FACTORY_CHAIN_LOCK_OWNER_THROUGHPUT_EXPECTED budget_ms=$P0_FACTORY_CHAIN_LOCK_OWNER_BUDGET stop_condition=$P0_FACTORY_CHAIN_LOCK_OWNER_STOP_CONDITION hipotese_de_gargalo=lock_compartilhado_segura_produtor_p0 next_action=$P0_FACTORY_CHAIN_LOCK_NEXT_ACTION" >&2
}

p0_factory_chain_lock_single_line() {
	printf '%s' "$1" | tr '\r\n' '  '
}

p0_factory_chain_lock_write_meta() {
	P0_FACTORY_CHAIN_LOCK_ACQUIRED_EPOCH="$1"
	P0_FACTORY_CHAIN_BUDGET_MS="${WIKI_HEAVY_BUDGET_MS:-${P0_FACTORY_CHAIN_BUDGET_MS:-300000}}"
	P0_FACTORY_CHAIN_EXPECTED_DURATION_MS="${WIKI_HEAVY_EXPECTED_DURATION_MS:-${P0_FACTORY_CHAIN_EXPECTED_DURATION_MS:-60000}}"
	P0_FACTORY_CHAIN_STOP_CONDITION="${WIKI_HEAVY_STOP_CONDITION:-${P0_FACTORY_CHAIN_STOP_CONDITION:-factory_chain_command_completed_or_failed_without_public_write}}"
	P0_FACTORY_CHAIN_THROUGHPUT_EXPECTED="${WIKI_HEAVY_THROUGHPUT_EXPECTED:-${P0_FACTORY_CHAIN_THROUGHPUT_EXPECTED:-timings_required_records_or_artifacts_per_second_when_available}}"
	P0_FACTORY_CHAIN_ARTIFACT_CLAIM_PATH="${WIKI_HEAVY_ARTIFACT_CLAIM_PATH:-none}"
	P0_FACTORY_CHAIN_ARTIFACT_CLAIM_PRODUCER="${WIKI_HEAVY_ARTIFACT_CLAIM_PRODUCER:-none}"
	P0_FACTORY_CHAIN_ARTIFACT_OUTPUT_FINGERPRINT_EXPECTED="${WIKI_HEAVY_ARTIFACT_OUTPUT_FINGERPRINT_EXPECTED:-none}"
	P0_FACTORY_CHAIN_LOCK_META_TEMP="$(mktemp "$P0_FACTORY_CHAIN_LOCK_DIR/.p0-factory-chain.lock.meta.XXXXXX")" || {
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: cannot allocate private lock metadata" >&2
		exit 75
	}
	if ! chmod 0600 "$P0_FACTORY_CHAIN_LOCK_META_TEMP"; then
		rm -f -- "$P0_FACTORY_CHAIN_LOCK_META_TEMP"
		exit 75
	fi
	{
		printf 'pid=%s\n' "$$"
		printf 'ppid=%s\n' "${PPID:-missing}"
		printf 'child_pid=%s\n' "missing"
		printf 'child_command=%s\n' "exec_or_shell_owner_pending"
		printf 'command=%s\n' "$(p0_factory_chain_lock_single_line "$P0_FACTORY_CHAIN_LOCK_COMMAND")"
		printf 'repository_root=%s\n' "$P0_FACTORY_CHAIN_REPO_CANONICAL"
		printf 'repository_identity=%s\n' "$P0_FACTORY_CHAIN_REPO_IDENTITY"
		printf 'lock_domain_schema=%s\n' "p0-factory-chain-lock-domain/v3-scoped"
		printf 'lock_domain=%s\n' "$(p0_factory_chain_lock_single_line "$P0_FACTORY_CHAIN_LOCK_DOMAIN")"
		printf 'coordination_path=%s\n' "$P0_FACTORY_CHAIN_COORDINATION_PATH"
		printf 'coordination_mode=%s\n' "$P0_FACTORY_CHAIN_COORDINATION_MODE"
		printf 'lifecycle_owner=%s\n' "tools/supervise-process-tree"
		printf 'started_epoch=%s\n' "$P0_FACTORY_CHAIN_LOCK_START_EPOCH"
		printf 'acquired_epoch=%s\n' "$P0_FACTORY_CHAIN_LOCK_ACQUIRED_EPOCH"
		printf 'lock_path=%s\n' "$P0_FACTORY_CHAIN_LOCK_PATH"
		printf 'budget_ms=%s\n' "$P0_FACTORY_CHAIN_BUDGET_MS"
		printf 'expected_duration_ms=%s\n' "$P0_FACTORY_CHAIN_EXPECTED_DURATION_MS"
		printf 'stop_condition=%s\n' "$(p0_factory_chain_lock_single_line "$P0_FACTORY_CHAIN_STOP_CONDITION")"
		printf 'throughput_expected=%s\n' "$(p0_factory_chain_lock_single_line "$P0_FACTORY_CHAIN_THROUGHPUT_EXPECTED")"
		printf 'lock_scope=%s\n' "$(p0_factory_chain_lock_single_line "${WIKI_HEAVY_LOCK_SCOPE:-p0-factory-chain}")"
		printf 'artifact_claim_path=%s\n' "$(p0_factory_chain_lock_single_line "$P0_FACTORY_CHAIN_ARTIFACT_CLAIM_PATH")"
		printf 'artifact_claim_producer=%s\n' "$(p0_factory_chain_lock_single_line "$P0_FACTORY_CHAIN_ARTIFACT_CLAIM_PRODUCER")"
		printf 'artifact_claim_output_fingerprint_expected=%s\n' "$(p0_factory_chain_lock_single_line "$P0_FACTORY_CHAIN_ARTIFACT_OUTPUT_FINGERPRINT_EXPECTED")"
	} >"$P0_FACTORY_CHAIN_LOCK_META_TEMP" || {
		rm -f -- "$P0_FACTORY_CHAIN_LOCK_META_TEMP"
		exit 75
	}
	if ! mv -f -- "$P0_FACTORY_CHAIN_LOCK_META_TEMP" "$P0_FACTORY_CHAIN_LOCK_META_PATH" ||
		[ -L "$P0_FACTORY_CHAIN_LOCK_META_PATH" ] ||
		[ ! -f "$P0_FACTORY_CHAIN_LOCK_META_PATH" ] ||
		[ "$(stat -Lc '%u:%a' "$P0_FACTORY_CHAIN_LOCK_META_PATH" 2>/dev/null || true)" != "$(id -u):600" ]; then
		rm -f -- "$P0_FACTORY_CHAIN_LOCK_META_TEMP"
		echo "$P0_FACTORY_CHAIN_LOCK_COMMAND: cannot install authenticated lock metadata" >&2
		exit 75
	fi
}
