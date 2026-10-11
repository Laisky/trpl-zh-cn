The chapter dependency regressions preserve the Rust 1.58 teaching baseline.
After fetching the locked dependencies for the eight examples listed in
test_guessing_examples.py, run:

~~~sh
CARGO=cargo TEST_BUILD_DIR=/tmp/book-regression-targets \
python3 -m unittest discover -s tests -v
~~~

Builds use --locked --offline and run serially. Listing 2-4 is intentionally
unable to compile: its string-versus-number type mismatch is part of the text.
The test requires the same E0308 diagnosis rather than repairing that lesson.
The seven runnable examples retain their stage-specific parse errors, looping,
quit-on-win and invalid-input recovery. No source listing is changed.
