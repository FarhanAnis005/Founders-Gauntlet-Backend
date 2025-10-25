-- CreateEnum
CREATE TYPE "PitchStatus" AS ENUM ('uploaded', 'processing', 'ready', 'failed');

-- CreateTable
CREATE TABLE "Pitch" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "updatedAt" TIMESTAMP(3) NOT NULL,
    "ownerClerkId" TEXT NOT NULL,
    "originalName" TEXT NOT NULL,
    "uploadPath" TEXT NOT NULL,
    "persona" TEXT NOT NULL,
    "status" "PitchStatus" NOT NULL DEFAULT 'uploaded',
    "error" TEXT,

    CONSTRAINT "Pitch_pkey" PRIMARY KEY ("id")
);

-- CreateTable
CREATE TABLE "DeckAnalysis" (
    "id" TEXT NOT NULL,
    "createdAt" TIMESTAMP(3) NOT NULL DEFAULT CURRENT_TIMESTAMP,
    "pitchId" TEXT NOT NULL,
    "resultJson" JSONB NOT NULL,

    CONSTRAINT "DeckAnalysis_pkey" PRIMARY KEY ("id")
);

-- CreateIndex
CREATE INDEX "Pitch_ownerClerkId_idx" ON "Pitch"("ownerClerkId");

-- CreateIndex
CREATE INDEX "Pitch_status_idx" ON "Pitch"("status");

-- AddForeignKey
ALTER TABLE "DeckAnalysis" ADD CONSTRAINT "DeckAnalysis_pitchId_fkey" FOREIGN KEY ("pitchId") REFERENCES "Pitch"("id") ON DELETE CASCADE ON UPDATE CASCADE;
