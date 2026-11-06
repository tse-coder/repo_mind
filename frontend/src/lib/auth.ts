import { betterAuth } from "better-auth";
import { username, jwt } from "better-auth/plugins";
import { Pool } from "pg";

const getDatabaseConfig = () => {
  if (process.env.DATABASE_URL) {
    return new Pool({
      connectionString: process.env.DATABASE_URL,
      ssl: process.env.DATABASE_SSL === "false" ? false : { rejectUnauthorized: false },
    });
  }
  return undefined;
};

export const auth = betterAuth({
  baseURL: process.env.BETTER_AUTH_URL || process.env.NEXT_PUBLIC_APP_URL || "http://localhost:3000",
  secret: process.env.BETTER_AUTH_SECRET || "repomind-development-secret-key-change-in-production-1234567890",
  database: getDatabaseConfig(),
  emailAndPassword: {
    enabled: true,
  },
  socialProviders: {
    google: {
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
      enabled: Boolean(process.env.GOOGLE_CLIENT_ID && process.env.GOOGLE_CLIENT_SECRET),
    },
  },
  plugins: [
    username(),
    jwt({
      jwt: {
        issuer: "repomind-app",
        audience: "repomind-api",
      },
    }),
  ],
});
