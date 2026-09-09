export const ENV = {

  API_URL: import.meta.env.VITE_API_URL || "/graphql/",
  IS_DEV: import.meta.env.MODE === "development",
};
