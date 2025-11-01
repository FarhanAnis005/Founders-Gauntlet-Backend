# agents/shark_agent.py
import os, json, pathlib
from dotenv import load_dotenv
from livekit.agents import JobContext, WorkerOptions, cli
from livekit.agents import voice
from livekit.plugins import google

async def entrypoint(ctx: JobContext):
    md = {}
    if ctx.job and ctx.job.metadata:
        try:
            md = json.loads(ctx.job.metadata)
        except Exception:
            pass

    persona = md.get("persona", "mark")
    instructions = md.get("instructions", "You are a helpful assistant.")
    voice_name = md.get("voice", "Puck")

    model = google.realtime.RealtimeModel(
        model="gemini-live-2.5-flash-preview",
        voice=voice_name,
        temperature=0.8,
        instructions=instructions,
    )
    agent = voice.Agent(instructions=instructions)
    session = voice.AgentSession(llm=model)
    await ctx.connect()
    await session.start(agent=agent, room=ctx.room)
    await session.run()

if __name__ == "__main__":
    load_dotenv(pathlib.Path(__file__).resolve().parents[1] / ".env")

    # This older form only takes the entrypoint function.
    opts = WorkerOptions(entrypoint_fnc=entrypoint)
    cli.run_app(opts)
