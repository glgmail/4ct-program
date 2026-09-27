# search/

Unavoidable-set search, learned discharging, and conjecture mining
(workstreams B and F).

A search is a result only when its output reruns identically from a clean
checkout. That means:

- a fixed random seed, recorded in the output;
- the toolchain and data commit recorded in the output header;
- the command line that produced it recorded next to it in `notes/`.

Heavy searches run on the self-hosted 32 GB runner. Cap parallelism with the
`JOBS` and `MEMORY` environment variables the runner sets, so peak memory
stays under 32 GB.
