
export const config = {
      "BASE_API_URL": import.meta.env.VITE_BASE_URL
}

for (const key in config){
      console.log(`CONFIG KEY: ${key} has value ${config[key]}`)
}