# tools/: deterministic domain tools

ponytail runs at level `lite` here, not `full`: explicit, boring code beats short code.
Every formula carries its source in a comment (textbook or standard, with the equation
number; never copied table text). Tools are tested on textbook cases, never on dev-task
values. A tool must run within 2 CPUs and 4 GB, or be written into the task container
with `write_file` and run there.
