import { Client } from "@langchain/langgraph-sdk";

export const client = new Client({
  apiUrl: "http://127.0.0.1:2024",
});
