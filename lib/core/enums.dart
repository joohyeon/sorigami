/// Drive upload lifecycle for a recording.
enum UploadStatus { none, queued, uploading, done, failed }

/// AI pipeline job lifecycle for a recording.
enum JobStatus { none, requested, processing, completed, failed }

/// What a Skill produces from the transcript.
enum OutputType { summary, tasks, both, custom }

/// Tone of the Skill's AI output.
enum Tone { formal, casual, concise }
