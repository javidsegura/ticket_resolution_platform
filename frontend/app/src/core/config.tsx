type Config = {
  BASE_API_URL: string | undefined;
};

export const config: Config = {
  BASE_API_URL: import.meta.env.VITE_BASE_URL,
};

for (const [key, value] of Object.entries(config)) {
  console.log(`CONFIG KEY: ${key} has value ${value}`);
}
