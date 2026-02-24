import yaml from "js-yaml";
import { ValidationError } from "../errors/exceptions.js";
import { ErrorCode } from "../errors/error-codes.js";

export function parseYAML(content: string): Record<string, unknown> {
  try {
    const result = yaml.load(content);
    if (typeof result !== "object" || result === null) {
      throw new ValidationError(ErrorCode.VAL014, "yaml_data", {
        details: "YAML content must be an object",
      });
    }
    return result as Record<string, unknown>;
  } catch (e) {
    if (e instanceof ValidationError) throw e;
    throw new ValidationError(ErrorCode.VAL014, "yaml_data", {
      details: String(e),
    });
  }
}
