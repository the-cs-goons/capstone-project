import axios from 'axios';

const walletBackendClient = axios.create({
    baseURL: `https://holder-lib:${process.env.CS3900_HOLDER_AGENT_PORT}`
});
  
export { walletBackendClient }