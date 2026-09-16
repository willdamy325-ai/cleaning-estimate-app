import { neon, type NeonQueryFunction } from "@neondatabase/serverless";

export class DatabaseConfigurationError extends Error {
  constructor() {
    super("データベース接続が設定されていません");
    this.name = "DatabaseConfigurationError";
  }
}

let client: NeonQueryFunction<false, false> | null = null;

export function getDatabase(): NeonQueryFunction<false, false> {
  if (client) {
    return client;
  }

  const connectionString = process.env.DATABASE_URL ?? process.env.POSTGRES_URL;
  if (!connectionString) {
    throw new DatabaseConfigurationError();
  }

  client = neon(connectionString);
  return client;
}
