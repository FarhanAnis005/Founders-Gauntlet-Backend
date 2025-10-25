# view_full_analysis.py
import asyncio, json
from prisma import Prisma

PITCH_ID = "cmh51jfcn0000lj340ru0mmtq"  # <-- your pitch id

async def main():
    db = Prisma(); await db.connect()
    p = await db.pitch.find_unique(where={"id": PITCH_ID}, include={"analyses": True})
    if not p or not p.analyses:
        print("No analysis found.")
        await db.disconnect(); return

    analysis = sorted(p.analyses, key=lambda a: a.createdAt)[-1].resultJson
    print("Meta:", json.dumps(analysis["meta"], indent=2))
    print("\nOne-liner:\n", analysis.get("one_liner", ""))

    # Show a few bullets
    print("\nThemes:", analysis.get("themes", [])[:5])
    print("\nStrengths:", analysis.get("strengths", [])[:5])
    print("\nRisks:", analysis.get("risks", [])[:5])

    # Per-shark questions (first 3 each)
    q = analysis.get("questions_by_shark", {})
    for shark in ["kevin", "mark", "lori", "barbara", "robert"]:
        print(f"\n{shark.title()} (sample):")
        for item in q.get(shark, [])[:3]:
            print(" -", item)

    # Optional: dump to a file
    with open("analysis_result_full.json", "w", encoding="utf-8") as f:
        json.dump(analysis, f, indent=2)
    print("\nSaved to analysis_result_full.json")

    await db.disconnect()

asyncio.run(main())
