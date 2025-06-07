import { client } from "@/lib/langgraph";
import { zValidator } from "@hono/zod-validator";
import { Hono } from "hono";
import { streamSSE } from "hono/streaming";
import { z } from "zod";

const inputSchema = z.object({
  question: z.string().min(1).optional(),
  answer: z.string().min(1).optional(),
});

const eventSchema = z.object({
  event: z.string(),
  data: z.unknown(),
});

export const agentRoute = new Hono().post(
  "/run",
  zValidator("json", inputSchema),
  (c) => {
    const { question, answer } = c.req.valid("json");
    return streamSSE(c, async (stream) => {
      try {
        const thread = await client.threads.create();
        const run = client.runs.stream(thread.thread_id, "fact_checker", {
          input: {
            question:
              question ||
              "What are the primary causes of global warming and what does the IPCC state about human contribution?",
            answer:
              answer ||
              "The main drivers of recent global warming are greenhouse gas emissions from burning fossil fuels, deforestation, and industrial activities. The IPCC has stated that human activities have warmed the planet by about 1.0°C since pre-industrial times.",
          },
          streamSubgraphs: true,
          streamMode: ["updates"],
        });

        for await (const event of run) {
          try {
            const validatedEvent = eventSchema.parse(event);
            await stream.writeSSE({ data: JSON.stringify(validatedEvent) });
          } catch (error) {
            console.error("Invalid event structure:", error);
            await stream.writeSSE({
              data: JSON.stringify({
                event: "error",
                data: {
                  message: "Server received malformed event data",
                  run_id: "validation-error",
                },
              }),
            });
          }
        }
      } catch (error) {
        console.error("Server error:", error);
        await stream.writeSSE({
          data: JSON.stringify({
            event: "error",
            data: {
              message: (error as Error).message || "An unknown error occurred",
              run_id: "server-error",
            },
          }),
        });
      }
    });
  }
);
