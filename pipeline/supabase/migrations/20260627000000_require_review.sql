ALTER TABLE sg_skills
ADD COLUMN IF NOT EXISTS require_review bool NOT NULL DEFAULT false;
