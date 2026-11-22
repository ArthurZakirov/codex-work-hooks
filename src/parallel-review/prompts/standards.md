# Code organization review

Check the following conventions in the changed code.

- **Group related operations.** Keep statements that perform one step together. Use a blank line where the purpose changes, such as the transition from loading inputs to evaluating a decision.
- **Keep orchestration readable.** The entry point should read as a short sequence of named operations at a consistent level of detail. Move a coherent block of parsing, command execution, or persistence into a function when its name helps the reader follow that sequence.
- **Separate responsibilities.** In a CLI, keep argument parsing separate from output formatting. In the greeting example, this includes formatting the greeting.
- **Name decisions precisely.** Function and variable names should say what is assessed, compared or returned.
- **Keep imports side-effect free.** Run the CLI through its entry point.

## Reporting findings

For each finding, cite the relevant lines and explain which operations are hard to distinguish or follow. Skip hypothetical refactors.
