// GENERATED CODE - DO NOT MODIFY BY HAND

part of 'database.dart';

// ignore_for_file: type=lint
class $RecordingsTable extends Recordings
    with TableInfo<$RecordingsTable, Recording> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $RecordingsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _titleMeta = const VerificationMeta('title');
  @override
  late final GeneratedColumn<String> title = GeneratedColumn<String>(
    'title',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _memoMeta = const VerificationMeta('memo');
  @override
  late final GeneratedColumn<String> memo = GeneratedColumn<String>(
    'memo',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  @override
  late final GeneratedColumnWithTypeConverter<List<String>, String> tags =
      GeneratedColumn<String>(
        'tags',
        aliasedName,
        false,
        type: DriftSqlType.string,
        requiredDuringInsert: false,
        defaultValue: const Constant('[]'),
      ).withConverter<List<String>>($RecordingsTable.$convertertags);
  static const VerificationMeta _categoryMeta = const VerificationMeta(
    'category',
  );
  @override
  late final GeneratedColumn<String> category = GeneratedColumn<String>(
    'category',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _languageMeta = const VerificationMeta(
    'language',
  );
  @override
  late final GeneratedColumn<String> language = GeneratedColumn<String>(
    'language',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('auto'),
  );
  static const VerificationMeta _modeIdMeta = const VerificationMeta('modeId');
  @override
  late final GeneratedColumn<String> modeId = GeneratedColumn<String>(
    'mode_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _audioFilePathMeta = const VerificationMeta(
    'audioFilePath',
  );
  @override
  late final GeneratedColumn<String> audioFilePath = GeneratedColumn<String>(
    'audio_file_path',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _audioDurationMsMeta = const VerificationMeta(
    'audioDurationMs',
  );
  @override
  late final GeneratedColumn<int> audioDurationMs = GeneratedColumn<int>(
    'audio_duration_ms',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _audioFileSizeMeta = const VerificationMeta(
    'audioFileSize',
  );
  @override
  late final GeneratedColumn<int> audioFileSize = GeneratedColumn<int>(
    'audio_file_size',
    aliasedName,
    true,
    type: DriftSqlType.int,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _uploadStatusMeta = const VerificationMeta(
    'uploadStatus',
  );
  @override
  late final GeneratedColumn<String> uploadStatus = GeneratedColumn<String>(
    'upload_status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('none'),
  );
  static const VerificationMeta _driveFileIdMeta = const VerificationMeta(
    'driveFileId',
  );
  @override
  late final GeneratedColumn<String> driveFileId = GeneratedColumn<String>(
    'drive_file_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _jobIdMeta = const VerificationMeta('jobId');
  @override
  late final GeneratedColumn<String> jobId = GeneratedColumn<String>(
    'job_id',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _jobStatusMeta = const VerificationMeta(
    'jobStatus',
  );
  @override
  late final GeneratedColumn<String> jobStatus = GeneratedColumn<String>(
    'job_status',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('none'),
  );
  static const VerificationMeta _jobErrorMeta = const VerificationMeta(
    'jobError',
  );
  @override
  late final GeneratedColumn<String> jobError = GeneratedColumn<String>(
    'job_error',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _updatedAtMeta = const VerificationMeta(
    'updatedAt',
  );
  @override
  late final GeneratedColumn<DateTime> updatedAt = GeneratedColumn<DateTime>(
    'updated_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    title,
    memo,
    tags,
    category,
    language,
    modeId,
    audioFilePath,
    audioDurationMs,
    audioFileSize,
    uploadStatus,
    driveFileId,
    jobId,
    jobStatus,
    jobError,
    createdAt,
    updatedAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'recordings';
  @override
  VerificationContext validateIntegrity(
    Insertable<Recording> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('title')) {
      context.handle(
        _titleMeta,
        title.isAcceptableOrUnknown(data['title']!, _titleMeta),
      );
    } else if (isInserting) {
      context.missing(_titleMeta);
    }
    if (data.containsKey('memo')) {
      context.handle(
        _memoMeta,
        memo.isAcceptableOrUnknown(data['memo']!, _memoMeta),
      );
    }
    if (data.containsKey('category')) {
      context.handle(
        _categoryMeta,
        category.isAcceptableOrUnknown(data['category']!, _categoryMeta),
      );
    }
    if (data.containsKey('language')) {
      context.handle(
        _languageMeta,
        language.isAcceptableOrUnknown(data['language']!, _languageMeta),
      );
    }
    if (data.containsKey('mode_id')) {
      context.handle(
        _modeIdMeta,
        modeId.isAcceptableOrUnknown(data['mode_id']!, _modeIdMeta),
      );
    }
    if (data.containsKey('audio_file_path')) {
      context.handle(
        _audioFilePathMeta,
        audioFilePath.isAcceptableOrUnknown(
          data['audio_file_path']!,
          _audioFilePathMeta,
        ),
      );
    } else if (isInserting) {
      context.missing(_audioFilePathMeta);
    }
    if (data.containsKey('audio_duration_ms')) {
      context.handle(
        _audioDurationMsMeta,
        audioDurationMs.isAcceptableOrUnknown(
          data['audio_duration_ms']!,
          _audioDurationMsMeta,
        ),
      );
    }
    if (data.containsKey('audio_file_size')) {
      context.handle(
        _audioFileSizeMeta,
        audioFileSize.isAcceptableOrUnknown(
          data['audio_file_size']!,
          _audioFileSizeMeta,
        ),
      );
    }
    if (data.containsKey('upload_status')) {
      context.handle(
        _uploadStatusMeta,
        uploadStatus.isAcceptableOrUnknown(
          data['upload_status']!,
          _uploadStatusMeta,
        ),
      );
    }
    if (data.containsKey('drive_file_id')) {
      context.handle(
        _driveFileIdMeta,
        driveFileId.isAcceptableOrUnknown(
          data['drive_file_id']!,
          _driveFileIdMeta,
        ),
      );
    }
    if (data.containsKey('job_id')) {
      context.handle(
        _jobIdMeta,
        jobId.isAcceptableOrUnknown(data['job_id']!, _jobIdMeta),
      );
    }
    if (data.containsKey('job_status')) {
      context.handle(
        _jobStatusMeta,
        jobStatus.isAcceptableOrUnknown(data['job_status']!, _jobStatusMeta),
      );
    }
    if (data.containsKey('job_error')) {
      context.handle(
        _jobErrorMeta,
        jobError.isAcceptableOrUnknown(data['job_error']!, _jobErrorMeta),
      );
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    if (data.containsKey('updated_at')) {
      context.handle(
        _updatedAtMeta,
        updatedAt.isAcceptableOrUnknown(data['updated_at']!, _updatedAtMeta),
      );
    } else if (isInserting) {
      context.missing(_updatedAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Recording map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Recording(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      title: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}title'],
      )!,
      memo: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}memo'],
      ),
      tags: $RecordingsTable.$convertertags.fromSql(
        attachedDatabase.typeMapping.read(
          DriftSqlType.string,
          data['${effectivePrefix}tags'],
        )!,
      ),
      category: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}category'],
      ),
      language: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}language'],
      )!,
      modeId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}mode_id'],
      ),
      audioFilePath: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}audio_file_path'],
      )!,
      audioDurationMs: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}audio_duration_ms'],
      ),
      audioFileSize: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}audio_file_size'],
      ),
      uploadStatus: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}upload_status'],
      )!,
      driveFileId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}drive_file_id'],
      ),
      jobId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}job_id'],
      ),
      jobStatus: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}job_status'],
      )!,
      jobError: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}job_error'],
      ),
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}created_at'],
      )!,
      updatedAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}updated_at'],
      )!,
    );
  }

  @override
  $RecordingsTable createAlias(String alias) {
    return $RecordingsTable(attachedDatabase, alias);
  }

  static TypeConverter<List<String>, String> $convertertags =
      const StringListConverter();
}

class Recording extends DataClass implements Insertable<Recording> {
  final String id;
  final String title;
  final String? memo;
  final List<String> tags;
  final String? category;
  final String language;
  final String? modeId;
  final String audioFilePath;
  final int? audioDurationMs;
  final int? audioFileSize;
  final String uploadStatus;
  final String? driveFileId;
  final String? jobId;
  final String jobStatus;
  final String? jobError;
  final DateTime createdAt;
  final DateTime updatedAt;
  const Recording({
    required this.id,
    required this.title,
    this.memo,
    required this.tags,
    this.category,
    required this.language,
    this.modeId,
    required this.audioFilePath,
    this.audioDurationMs,
    this.audioFileSize,
    required this.uploadStatus,
    this.driveFileId,
    this.jobId,
    required this.jobStatus,
    this.jobError,
    required this.createdAt,
    required this.updatedAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['title'] = Variable<String>(title);
    if (!nullToAbsent || memo != null) {
      map['memo'] = Variable<String>(memo);
    }
    {
      map['tags'] = Variable<String>(
        $RecordingsTable.$convertertags.toSql(tags),
      );
    }
    if (!nullToAbsent || category != null) {
      map['category'] = Variable<String>(category);
    }
    map['language'] = Variable<String>(language);
    if (!nullToAbsent || modeId != null) {
      map['mode_id'] = Variable<String>(modeId);
    }
    map['audio_file_path'] = Variable<String>(audioFilePath);
    if (!nullToAbsent || audioDurationMs != null) {
      map['audio_duration_ms'] = Variable<int>(audioDurationMs);
    }
    if (!nullToAbsent || audioFileSize != null) {
      map['audio_file_size'] = Variable<int>(audioFileSize);
    }
    map['upload_status'] = Variable<String>(uploadStatus);
    if (!nullToAbsent || driveFileId != null) {
      map['drive_file_id'] = Variable<String>(driveFileId);
    }
    if (!nullToAbsent || jobId != null) {
      map['job_id'] = Variable<String>(jobId);
    }
    map['job_status'] = Variable<String>(jobStatus);
    if (!nullToAbsent || jobError != null) {
      map['job_error'] = Variable<String>(jobError);
    }
    map['created_at'] = Variable<DateTime>(createdAt);
    map['updated_at'] = Variable<DateTime>(updatedAt);
    return map;
  }

  RecordingsCompanion toCompanion(bool nullToAbsent) {
    return RecordingsCompanion(
      id: Value(id),
      title: Value(title),
      memo: memo == null && nullToAbsent ? const Value.absent() : Value(memo),
      tags: Value(tags),
      category: category == null && nullToAbsent
          ? const Value.absent()
          : Value(category),
      language: Value(language),
      modeId: modeId == null && nullToAbsent
          ? const Value.absent()
          : Value(modeId),
      audioFilePath: Value(audioFilePath),
      audioDurationMs: audioDurationMs == null && nullToAbsent
          ? const Value.absent()
          : Value(audioDurationMs),
      audioFileSize: audioFileSize == null && nullToAbsent
          ? const Value.absent()
          : Value(audioFileSize),
      uploadStatus: Value(uploadStatus),
      driveFileId: driveFileId == null && nullToAbsent
          ? const Value.absent()
          : Value(driveFileId),
      jobId: jobId == null && nullToAbsent
          ? const Value.absent()
          : Value(jobId),
      jobStatus: Value(jobStatus),
      jobError: jobError == null && nullToAbsent
          ? const Value.absent()
          : Value(jobError),
      createdAt: Value(createdAt),
      updatedAt: Value(updatedAt),
    );
  }

  factory Recording.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Recording(
      id: serializer.fromJson<String>(json['id']),
      title: serializer.fromJson<String>(json['title']),
      memo: serializer.fromJson<String?>(json['memo']),
      tags: serializer.fromJson<List<String>>(json['tags']),
      category: serializer.fromJson<String?>(json['category']),
      language: serializer.fromJson<String>(json['language']),
      modeId: serializer.fromJson<String?>(json['modeId']),
      audioFilePath: serializer.fromJson<String>(json['audioFilePath']),
      audioDurationMs: serializer.fromJson<int?>(json['audioDurationMs']),
      audioFileSize: serializer.fromJson<int?>(json['audioFileSize']),
      uploadStatus: serializer.fromJson<String>(json['uploadStatus']),
      driveFileId: serializer.fromJson<String?>(json['driveFileId']),
      jobId: serializer.fromJson<String?>(json['jobId']),
      jobStatus: serializer.fromJson<String>(json['jobStatus']),
      jobError: serializer.fromJson<String?>(json['jobError']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
      updatedAt: serializer.fromJson<DateTime>(json['updatedAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'title': serializer.toJson<String>(title),
      'memo': serializer.toJson<String?>(memo),
      'tags': serializer.toJson<List<String>>(tags),
      'category': serializer.toJson<String?>(category),
      'language': serializer.toJson<String>(language),
      'modeId': serializer.toJson<String?>(modeId),
      'audioFilePath': serializer.toJson<String>(audioFilePath),
      'audioDurationMs': serializer.toJson<int?>(audioDurationMs),
      'audioFileSize': serializer.toJson<int?>(audioFileSize),
      'uploadStatus': serializer.toJson<String>(uploadStatus),
      'driveFileId': serializer.toJson<String?>(driveFileId),
      'jobId': serializer.toJson<String?>(jobId),
      'jobStatus': serializer.toJson<String>(jobStatus),
      'jobError': serializer.toJson<String?>(jobError),
      'createdAt': serializer.toJson<DateTime>(createdAt),
      'updatedAt': serializer.toJson<DateTime>(updatedAt),
    };
  }

  Recording copyWith({
    String? id,
    String? title,
    Value<String?> memo = const Value.absent(),
    List<String>? tags,
    Value<String?> category = const Value.absent(),
    String? language,
    Value<String?> modeId = const Value.absent(),
    String? audioFilePath,
    Value<int?> audioDurationMs = const Value.absent(),
    Value<int?> audioFileSize = const Value.absent(),
    String? uploadStatus,
    Value<String?> driveFileId = const Value.absent(),
    Value<String?> jobId = const Value.absent(),
    String? jobStatus,
    Value<String?> jobError = const Value.absent(),
    DateTime? createdAt,
    DateTime? updatedAt,
  }) => Recording(
    id: id ?? this.id,
    title: title ?? this.title,
    memo: memo.present ? memo.value : this.memo,
    tags: tags ?? this.tags,
    category: category.present ? category.value : this.category,
    language: language ?? this.language,
    modeId: modeId.present ? modeId.value : this.modeId,
    audioFilePath: audioFilePath ?? this.audioFilePath,
    audioDurationMs: audioDurationMs.present
        ? audioDurationMs.value
        : this.audioDurationMs,
    audioFileSize: audioFileSize.present
        ? audioFileSize.value
        : this.audioFileSize,
    uploadStatus: uploadStatus ?? this.uploadStatus,
    driveFileId: driveFileId.present ? driveFileId.value : this.driveFileId,
    jobId: jobId.present ? jobId.value : this.jobId,
    jobStatus: jobStatus ?? this.jobStatus,
    jobError: jobError.present ? jobError.value : this.jobError,
    createdAt: createdAt ?? this.createdAt,
    updatedAt: updatedAt ?? this.updatedAt,
  );
  Recording copyWithCompanion(RecordingsCompanion data) {
    return Recording(
      id: data.id.present ? data.id.value : this.id,
      title: data.title.present ? data.title.value : this.title,
      memo: data.memo.present ? data.memo.value : this.memo,
      tags: data.tags.present ? data.tags.value : this.tags,
      category: data.category.present ? data.category.value : this.category,
      language: data.language.present ? data.language.value : this.language,
      modeId: data.modeId.present ? data.modeId.value : this.modeId,
      audioFilePath: data.audioFilePath.present
          ? data.audioFilePath.value
          : this.audioFilePath,
      audioDurationMs: data.audioDurationMs.present
          ? data.audioDurationMs.value
          : this.audioDurationMs,
      audioFileSize: data.audioFileSize.present
          ? data.audioFileSize.value
          : this.audioFileSize,
      uploadStatus: data.uploadStatus.present
          ? data.uploadStatus.value
          : this.uploadStatus,
      driveFileId: data.driveFileId.present
          ? data.driveFileId.value
          : this.driveFileId,
      jobId: data.jobId.present ? data.jobId.value : this.jobId,
      jobStatus: data.jobStatus.present ? data.jobStatus.value : this.jobStatus,
      jobError: data.jobError.present ? data.jobError.value : this.jobError,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
      updatedAt: data.updatedAt.present ? data.updatedAt.value : this.updatedAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Recording(')
          ..write('id: $id, ')
          ..write('title: $title, ')
          ..write('memo: $memo, ')
          ..write('tags: $tags, ')
          ..write('category: $category, ')
          ..write('language: $language, ')
          ..write('modeId: $modeId, ')
          ..write('audioFilePath: $audioFilePath, ')
          ..write('audioDurationMs: $audioDurationMs, ')
          ..write('audioFileSize: $audioFileSize, ')
          ..write('uploadStatus: $uploadStatus, ')
          ..write('driveFileId: $driveFileId, ')
          ..write('jobId: $jobId, ')
          ..write('jobStatus: $jobStatus, ')
          ..write('jobError: $jobError, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    title,
    memo,
    tags,
    category,
    language,
    modeId,
    audioFilePath,
    audioDurationMs,
    audioFileSize,
    uploadStatus,
    driveFileId,
    jobId,
    jobStatus,
    jobError,
    createdAt,
    updatedAt,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Recording &&
          other.id == this.id &&
          other.title == this.title &&
          other.memo == this.memo &&
          other.tags == this.tags &&
          other.category == this.category &&
          other.language == this.language &&
          other.modeId == this.modeId &&
          other.audioFilePath == this.audioFilePath &&
          other.audioDurationMs == this.audioDurationMs &&
          other.audioFileSize == this.audioFileSize &&
          other.uploadStatus == this.uploadStatus &&
          other.driveFileId == this.driveFileId &&
          other.jobId == this.jobId &&
          other.jobStatus == this.jobStatus &&
          other.jobError == this.jobError &&
          other.createdAt == this.createdAt &&
          other.updatedAt == this.updatedAt);
}

class RecordingsCompanion extends UpdateCompanion<Recording> {
  final Value<String> id;
  final Value<String> title;
  final Value<String?> memo;
  final Value<List<String>> tags;
  final Value<String?> category;
  final Value<String> language;
  final Value<String?> modeId;
  final Value<String> audioFilePath;
  final Value<int?> audioDurationMs;
  final Value<int?> audioFileSize;
  final Value<String> uploadStatus;
  final Value<String?> driveFileId;
  final Value<String?> jobId;
  final Value<String> jobStatus;
  final Value<String?> jobError;
  final Value<DateTime> createdAt;
  final Value<DateTime> updatedAt;
  final Value<int> rowid;
  const RecordingsCompanion({
    this.id = const Value.absent(),
    this.title = const Value.absent(),
    this.memo = const Value.absent(),
    this.tags = const Value.absent(),
    this.category = const Value.absent(),
    this.language = const Value.absent(),
    this.modeId = const Value.absent(),
    this.audioFilePath = const Value.absent(),
    this.audioDurationMs = const Value.absent(),
    this.audioFileSize = const Value.absent(),
    this.uploadStatus = const Value.absent(),
    this.driveFileId = const Value.absent(),
    this.jobId = const Value.absent(),
    this.jobStatus = const Value.absent(),
    this.jobError = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.updatedAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  RecordingsCompanion.insert({
    required String id,
    required String title,
    this.memo = const Value.absent(),
    this.tags = const Value.absent(),
    this.category = const Value.absent(),
    this.language = const Value.absent(),
    this.modeId = const Value.absent(),
    required String audioFilePath,
    this.audioDurationMs = const Value.absent(),
    this.audioFileSize = const Value.absent(),
    this.uploadStatus = const Value.absent(),
    this.driveFileId = const Value.absent(),
    this.jobId = const Value.absent(),
    this.jobStatus = const Value.absent(),
    this.jobError = const Value.absent(),
    required DateTime createdAt,
    required DateTime updatedAt,
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       title = Value(title),
       audioFilePath = Value(audioFilePath),
       createdAt = Value(createdAt),
       updatedAt = Value(updatedAt);
  static Insertable<Recording> custom({
    Expression<String>? id,
    Expression<String>? title,
    Expression<String>? memo,
    Expression<String>? tags,
    Expression<String>? category,
    Expression<String>? language,
    Expression<String>? modeId,
    Expression<String>? audioFilePath,
    Expression<int>? audioDurationMs,
    Expression<int>? audioFileSize,
    Expression<String>? uploadStatus,
    Expression<String>? driveFileId,
    Expression<String>? jobId,
    Expression<String>? jobStatus,
    Expression<String>? jobError,
    Expression<DateTime>? createdAt,
    Expression<DateTime>? updatedAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (title != null) 'title': title,
      if (memo != null) 'memo': memo,
      if (tags != null) 'tags': tags,
      if (category != null) 'category': category,
      if (language != null) 'language': language,
      if (modeId != null) 'mode_id': modeId,
      if (audioFilePath != null) 'audio_file_path': audioFilePath,
      if (audioDurationMs != null) 'audio_duration_ms': audioDurationMs,
      if (audioFileSize != null) 'audio_file_size': audioFileSize,
      if (uploadStatus != null) 'upload_status': uploadStatus,
      if (driveFileId != null) 'drive_file_id': driveFileId,
      if (jobId != null) 'job_id': jobId,
      if (jobStatus != null) 'job_status': jobStatus,
      if (jobError != null) 'job_error': jobError,
      if (createdAt != null) 'created_at': createdAt,
      if (updatedAt != null) 'updated_at': updatedAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  RecordingsCompanion copyWith({
    Value<String>? id,
    Value<String>? title,
    Value<String?>? memo,
    Value<List<String>>? tags,
    Value<String?>? category,
    Value<String>? language,
    Value<String?>? modeId,
    Value<String>? audioFilePath,
    Value<int?>? audioDurationMs,
    Value<int?>? audioFileSize,
    Value<String>? uploadStatus,
    Value<String?>? driveFileId,
    Value<String?>? jobId,
    Value<String>? jobStatus,
    Value<String?>? jobError,
    Value<DateTime>? createdAt,
    Value<DateTime>? updatedAt,
    Value<int>? rowid,
  }) {
    return RecordingsCompanion(
      id: id ?? this.id,
      title: title ?? this.title,
      memo: memo ?? this.memo,
      tags: tags ?? this.tags,
      category: category ?? this.category,
      language: language ?? this.language,
      modeId: modeId ?? this.modeId,
      audioFilePath: audioFilePath ?? this.audioFilePath,
      audioDurationMs: audioDurationMs ?? this.audioDurationMs,
      audioFileSize: audioFileSize ?? this.audioFileSize,
      uploadStatus: uploadStatus ?? this.uploadStatus,
      driveFileId: driveFileId ?? this.driveFileId,
      jobId: jobId ?? this.jobId,
      jobStatus: jobStatus ?? this.jobStatus,
      jobError: jobError ?? this.jobError,
      createdAt: createdAt ?? this.createdAt,
      updatedAt: updatedAt ?? this.updatedAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (title.present) {
      map['title'] = Variable<String>(title.value);
    }
    if (memo.present) {
      map['memo'] = Variable<String>(memo.value);
    }
    if (tags.present) {
      map['tags'] = Variable<String>(
        $RecordingsTable.$convertertags.toSql(tags.value),
      );
    }
    if (category.present) {
      map['category'] = Variable<String>(category.value);
    }
    if (language.present) {
      map['language'] = Variable<String>(language.value);
    }
    if (modeId.present) {
      map['mode_id'] = Variable<String>(modeId.value);
    }
    if (audioFilePath.present) {
      map['audio_file_path'] = Variable<String>(audioFilePath.value);
    }
    if (audioDurationMs.present) {
      map['audio_duration_ms'] = Variable<int>(audioDurationMs.value);
    }
    if (audioFileSize.present) {
      map['audio_file_size'] = Variable<int>(audioFileSize.value);
    }
    if (uploadStatus.present) {
      map['upload_status'] = Variable<String>(uploadStatus.value);
    }
    if (driveFileId.present) {
      map['drive_file_id'] = Variable<String>(driveFileId.value);
    }
    if (jobId.present) {
      map['job_id'] = Variable<String>(jobId.value);
    }
    if (jobStatus.present) {
      map['job_status'] = Variable<String>(jobStatus.value);
    }
    if (jobError.present) {
      map['job_error'] = Variable<String>(jobError.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (updatedAt.present) {
      map['updated_at'] = Variable<DateTime>(updatedAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('RecordingsCompanion(')
          ..write('id: $id, ')
          ..write('title: $title, ')
          ..write('memo: $memo, ')
          ..write('tags: $tags, ')
          ..write('category: $category, ')
          ..write('language: $language, ')
          ..write('modeId: $modeId, ')
          ..write('audioFilePath: $audioFilePath, ')
          ..write('audioDurationMs: $audioDurationMs, ')
          ..write('audioFileSize: $audioFileSize, ')
          ..write('uploadStatus: $uploadStatus, ')
          ..write('driveFileId: $driveFileId, ')
          ..write('jobId: $jobId, ')
          ..write('jobStatus: $jobStatus, ')
          ..write('jobError: $jobError, ')
          ..write('createdAt: $createdAt, ')
          ..write('updatedAt: $updatedAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $ModesTable extends Modes with TableInfo<$ModesTable, Mode> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ModesTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
    'name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _iconMeta = const VerificationMeta('icon');
  @override
  late final GeneratedColumn<String> icon = GeneratedColumn<String>(
    'icon',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _isDefaultMeta = const VerificationMeta(
    'isDefault',
  );
  @override
  late final GeneratedColumn<bool> isDefault = GeneratedColumn<bool>(
    'is_default',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("is_default" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  static const VerificationMeta _isSeededMeta = const VerificationMeta(
    'isSeeded',
  );
  @override
  late final GeneratedColumn<bool> isSeeded = GeneratedColumn<bool>(
    'is_seeded',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("is_seeded" IN (0, 1))',
    ),
    defaultValue: const Constant(false),
  );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    name,
    icon,
    isDefault,
    isSeeded,
    createdAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'modes';
  @override
  VerificationContext validateIntegrity(
    Insertable<Mode> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
        _nameMeta,
        name.isAcceptableOrUnknown(data['name']!, _nameMeta),
      );
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('icon')) {
      context.handle(
        _iconMeta,
        icon.isAcceptableOrUnknown(data['icon']!, _iconMeta),
      );
    } else if (isInserting) {
      context.missing(_iconMeta);
    }
    if (data.containsKey('is_default')) {
      context.handle(
        _isDefaultMeta,
        isDefault.isAcceptableOrUnknown(data['is_default']!, _isDefaultMeta),
      );
    }
    if (data.containsKey('is_seeded')) {
      context.handle(
        _isSeededMeta,
        isSeeded.isAcceptableOrUnknown(data['is_seeded']!, _isSeededMeta),
      );
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Mode map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Mode(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      name: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}name'],
      )!,
      icon: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}icon'],
      )!,
      isDefault: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}is_default'],
      )!,
      isSeeded: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}is_seeded'],
      )!,
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}created_at'],
      )!,
    );
  }

  @override
  $ModesTable createAlias(String alias) {
    return $ModesTable(attachedDatabase, alias);
  }
}

class Mode extends DataClass implements Insertable<Mode> {
  final String id;
  final String name;
  final String icon;
  final bool isDefault;
  final bool isSeeded;
  final DateTime createdAt;
  const Mode({
    required this.id,
    required this.name,
    required this.icon,
    required this.isDefault,
    required this.isSeeded,
    required this.createdAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['name'] = Variable<String>(name);
    map['icon'] = Variable<String>(icon);
    map['is_default'] = Variable<bool>(isDefault);
    map['is_seeded'] = Variable<bool>(isSeeded);
    map['created_at'] = Variable<DateTime>(createdAt);
    return map;
  }

  ModesCompanion toCompanion(bool nullToAbsent) {
    return ModesCompanion(
      id: Value(id),
      name: Value(name),
      icon: Value(icon),
      isDefault: Value(isDefault),
      isSeeded: Value(isSeeded),
      createdAt: Value(createdAt),
    );
  }

  factory Mode.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Mode(
      id: serializer.fromJson<String>(json['id']),
      name: serializer.fromJson<String>(json['name']),
      icon: serializer.fromJson<String>(json['icon']),
      isDefault: serializer.fromJson<bool>(json['isDefault']),
      isSeeded: serializer.fromJson<bool>(json['isSeeded']),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'name': serializer.toJson<String>(name),
      'icon': serializer.toJson<String>(icon),
      'isDefault': serializer.toJson<bool>(isDefault),
      'isSeeded': serializer.toJson<bool>(isSeeded),
      'createdAt': serializer.toJson<DateTime>(createdAt),
    };
  }

  Mode copyWith({
    String? id,
    String? name,
    String? icon,
    bool? isDefault,
    bool? isSeeded,
    DateTime? createdAt,
  }) => Mode(
    id: id ?? this.id,
    name: name ?? this.name,
    icon: icon ?? this.icon,
    isDefault: isDefault ?? this.isDefault,
    isSeeded: isSeeded ?? this.isSeeded,
    createdAt: createdAt ?? this.createdAt,
  );
  Mode copyWithCompanion(ModesCompanion data) {
    return Mode(
      id: data.id.present ? data.id.value : this.id,
      name: data.name.present ? data.name.value : this.name,
      icon: data.icon.present ? data.icon.value : this.icon,
      isDefault: data.isDefault.present ? data.isDefault.value : this.isDefault,
      isSeeded: data.isSeeded.present ? data.isSeeded.value : this.isSeeded,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Mode(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('icon: $icon, ')
          ..write('isDefault: $isDefault, ')
          ..write('isSeeded: $isSeeded, ')
          ..write('createdAt: $createdAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode =>
      Object.hash(id, name, icon, isDefault, isSeeded, createdAt);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Mode &&
          other.id == this.id &&
          other.name == this.name &&
          other.icon == this.icon &&
          other.isDefault == this.isDefault &&
          other.isSeeded == this.isSeeded &&
          other.createdAt == this.createdAt);
}

class ModesCompanion extends UpdateCompanion<Mode> {
  final Value<String> id;
  final Value<String> name;
  final Value<String> icon;
  final Value<bool> isDefault;
  final Value<bool> isSeeded;
  final Value<DateTime> createdAt;
  final Value<int> rowid;
  const ModesCompanion({
    this.id = const Value.absent(),
    this.name = const Value.absent(),
    this.icon = const Value.absent(),
    this.isDefault = const Value.absent(),
    this.isSeeded = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  ModesCompanion.insert({
    required String id,
    required String name,
    required String icon,
    this.isDefault = const Value.absent(),
    this.isSeeded = const Value.absent(),
    required DateTime createdAt,
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       name = Value(name),
       icon = Value(icon),
       createdAt = Value(createdAt);
  static Insertable<Mode> custom({
    Expression<String>? id,
    Expression<String>? name,
    Expression<String>? icon,
    Expression<bool>? isDefault,
    Expression<bool>? isSeeded,
    Expression<DateTime>? createdAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (name != null) 'name': name,
      if (icon != null) 'icon': icon,
      if (isDefault != null) 'is_default': isDefault,
      if (isSeeded != null) 'is_seeded': isSeeded,
      if (createdAt != null) 'created_at': createdAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  ModesCompanion copyWith({
    Value<String>? id,
    Value<String>? name,
    Value<String>? icon,
    Value<bool>? isDefault,
    Value<bool>? isSeeded,
    Value<DateTime>? createdAt,
    Value<int>? rowid,
  }) {
    return ModesCompanion(
      id: id ?? this.id,
      name: name ?? this.name,
      icon: icon ?? this.icon,
      isDefault: isDefault ?? this.isDefault,
      isSeeded: isSeeded ?? this.isSeeded,
      createdAt: createdAt ?? this.createdAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (icon.present) {
      map['icon'] = Variable<String>(icon.value);
    }
    if (isDefault.present) {
      map['is_default'] = Variable<bool>(isDefault.value);
    }
    if (isSeeded.present) {
      map['is_seeded'] = Variable<bool>(isSeeded.value);
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ModesCompanion(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('icon: $icon, ')
          ..write('isDefault: $isDefault, ')
          ..write('isSeeded: $isSeeded, ')
          ..write('createdAt: $createdAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $SkillsTable extends Skills with TableInfo<$SkillsTable, Skill> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $SkillsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _idMeta = const VerificationMeta('id');
  @override
  late final GeneratedColumn<String> id = GeneratedColumn<String>(
    'id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _nameMeta = const VerificationMeta('name');
  @override
  late final GeneratedColumn<String> name = GeneratedColumn<String>(
    'name',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _descriptionMeta = const VerificationMeta(
    'description',
  );
  @override
  late final GeneratedColumn<String> description = GeneratedColumn<String>(
    'description',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _languageMeta = const VerificationMeta(
    'language',
  );
  @override
  late final GeneratedColumn<String> language = GeneratedColumn<String>(
    'language',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('auto'),
  );
  static const VerificationMeta _identifySpeakersMeta = const VerificationMeta(
    'identifySpeakers',
  );
  @override
  late final GeneratedColumn<bool> identifySpeakers = GeneratedColumn<bool>(
    'identify_speakers',
    aliasedName,
    false,
    type: DriftSqlType.bool,
    requiredDuringInsert: false,
    defaultConstraints: GeneratedColumn.constraintIsAlways(
      'CHECK ("identify_speakers" IN (0, 1))',
    ),
    defaultValue: const Constant(true),
  );
  @override
  late final GeneratedColumnWithTypeConverter<List<String>, String>
  vocabularyHints = GeneratedColumn<String>(
    'vocabulary_hints',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('[]'),
  ).withConverter<List<String>>($SkillsTable.$convertervocabularyHints);
  static const VerificationMeta _outputTypeMeta = const VerificationMeta(
    'outputType',
  );
  @override
  late final GeneratedColumn<String> outputType = GeneratedColumn<String>(
    'output_type',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('summary'),
  );
  static const VerificationMeta _focusAreaMeta = const VerificationMeta(
    'focusArea',
  );
  @override
  late final GeneratedColumn<String> focusArea = GeneratedColumn<String>(
    'focus_area',
    aliasedName,
    true,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
  );
  static const VerificationMeta _toneMeta = const VerificationMeta('tone');
  @override
  late final GeneratedColumn<String> tone = GeneratedColumn<String>(
    'tone',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('concise'),
  );
  static const VerificationMeta _outputLanguageMeta = const VerificationMeta(
    'outputLanguage',
  );
  @override
  late final GeneratedColumn<String> outputLanguage = GeneratedColumn<String>(
    'output_language',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: false,
    defaultValue: const Constant('auto'),
  );
  static const VerificationMeta _additionalInstructionsMeta =
      const VerificationMeta('additionalInstructions');
  @override
  late final GeneratedColumn<String> additionalInstructions =
      GeneratedColumn<String>(
        'additional_instructions',
        aliasedName,
        true,
        type: DriftSqlType.string,
        requiredDuringInsert: false,
      );
  static const VerificationMeta _createdAtMeta = const VerificationMeta(
    'createdAt',
  );
  @override
  late final GeneratedColumn<DateTime> createdAt = GeneratedColumn<DateTime>(
    'created_at',
    aliasedName,
    false,
    type: DriftSqlType.dateTime,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [
    id,
    name,
    description,
    language,
    identifySpeakers,
    vocabularyHints,
    outputType,
    focusArea,
    tone,
    outputLanguage,
    additionalInstructions,
    createdAt,
  ];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'skills';
  @override
  VerificationContext validateIntegrity(
    Insertable<Skill> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('id')) {
      context.handle(_idMeta, id.isAcceptableOrUnknown(data['id']!, _idMeta));
    } else if (isInserting) {
      context.missing(_idMeta);
    }
    if (data.containsKey('name')) {
      context.handle(
        _nameMeta,
        name.isAcceptableOrUnknown(data['name']!, _nameMeta),
      );
    } else if (isInserting) {
      context.missing(_nameMeta);
    }
    if (data.containsKey('description')) {
      context.handle(
        _descriptionMeta,
        description.isAcceptableOrUnknown(
          data['description']!,
          _descriptionMeta,
        ),
      );
    }
    if (data.containsKey('language')) {
      context.handle(
        _languageMeta,
        language.isAcceptableOrUnknown(data['language']!, _languageMeta),
      );
    }
    if (data.containsKey('identify_speakers')) {
      context.handle(
        _identifySpeakersMeta,
        identifySpeakers.isAcceptableOrUnknown(
          data['identify_speakers']!,
          _identifySpeakersMeta,
        ),
      );
    }
    if (data.containsKey('output_type')) {
      context.handle(
        _outputTypeMeta,
        outputType.isAcceptableOrUnknown(data['output_type']!, _outputTypeMeta),
      );
    }
    if (data.containsKey('focus_area')) {
      context.handle(
        _focusAreaMeta,
        focusArea.isAcceptableOrUnknown(data['focus_area']!, _focusAreaMeta),
      );
    }
    if (data.containsKey('tone')) {
      context.handle(
        _toneMeta,
        tone.isAcceptableOrUnknown(data['tone']!, _toneMeta),
      );
    }
    if (data.containsKey('output_language')) {
      context.handle(
        _outputLanguageMeta,
        outputLanguage.isAcceptableOrUnknown(
          data['output_language']!,
          _outputLanguageMeta,
        ),
      );
    }
    if (data.containsKey('additional_instructions')) {
      context.handle(
        _additionalInstructionsMeta,
        additionalInstructions.isAcceptableOrUnknown(
          data['additional_instructions']!,
          _additionalInstructionsMeta,
        ),
      );
    }
    if (data.containsKey('created_at')) {
      context.handle(
        _createdAtMeta,
        createdAt.isAcceptableOrUnknown(data['created_at']!, _createdAtMeta),
      );
    } else if (isInserting) {
      context.missing(_createdAtMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {id};
  @override
  Skill map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return Skill(
      id: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}id'],
      )!,
      name: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}name'],
      )!,
      description: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}description'],
      ),
      language: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}language'],
      )!,
      identifySpeakers: attachedDatabase.typeMapping.read(
        DriftSqlType.bool,
        data['${effectivePrefix}identify_speakers'],
      )!,
      vocabularyHints: $SkillsTable.$convertervocabularyHints.fromSql(
        attachedDatabase.typeMapping.read(
          DriftSqlType.string,
          data['${effectivePrefix}vocabulary_hints'],
        )!,
      ),
      outputType: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}output_type'],
      )!,
      focusArea: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}focus_area'],
      ),
      tone: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}tone'],
      )!,
      outputLanguage: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}output_language'],
      )!,
      additionalInstructions: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}additional_instructions'],
      ),
      createdAt: attachedDatabase.typeMapping.read(
        DriftSqlType.dateTime,
        data['${effectivePrefix}created_at'],
      )!,
    );
  }

  @override
  $SkillsTable createAlias(String alias) {
    return $SkillsTable(attachedDatabase, alias);
  }

  static TypeConverter<List<String>, String> $convertervocabularyHints =
      const StringListConverter();
}

class Skill extends DataClass implements Insertable<Skill> {
  final String id;
  final String name;
  final String? description;
  final String language;
  final bool identifySpeakers;
  final List<String> vocabularyHints;
  final String outputType;
  final String? focusArea;
  final String tone;
  final String outputLanguage;
  final String? additionalInstructions;
  final DateTime createdAt;
  const Skill({
    required this.id,
    required this.name,
    this.description,
    required this.language,
    required this.identifySpeakers,
    required this.vocabularyHints,
    required this.outputType,
    this.focusArea,
    required this.tone,
    required this.outputLanguage,
    this.additionalInstructions,
    required this.createdAt,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['id'] = Variable<String>(id);
    map['name'] = Variable<String>(name);
    if (!nullToAbsent || description != null) {
      map['description'] = Variable<String>(description);
    }
    map['language'] = Variable<String>(language);
    map['identify_speakers'] = Variable<bool>(identifySpeakers);
    {
      map['vocabulary_hints'] = Variable<String>(
        $SkillsTable.$convertervocabularyHints.toSql(vocabularyHints),
      );
    }
    map['output_type'] = Variable<String>(outputType);
    if (!nullToAbsent || focusArea != null) {
      map['focus_area'] = Variable<String>(focusArea);
    }
    map['tone'] = Variable<String>(tone);
    map['output_language'] = Variable<String>(outputLanguage);
    if (!nullToAbsent || additionalInstructions != null) {
      map['additional_instructions'] = Variable<String>(additionalInstructions);
    }
    map['created_at'] = Variable<DateTime>(createdAt);
    return map;
  }

  SkillsCompanion toCompanion(bool nullToAbsent) {
    return SkillsCompanion(
      id: Value(id),
      name: Value(name),
      description: description == null && nullToAbsent
          ? const Value.absent()
          : Value(description),
      language: Value(language),
      identifySpeakers: Value(identifySpeakers),
      vocabularyHints: Value(vocabularyHints),
      outputType: Value(outputType),
      focusArea: focusArea == null && nullToAbsent
          ? const Value.absent()
          : Value(focusArea),
      tone: Value(tone),
      outputLanguage: Value(outputLanguage),
      additionalInstructions: additionalInstructions == null && nullToAbsent
          ? const Value.absent()
          : Value(additionalInstructions),
      createdAt: Value(createdAt),
    );
  }

  factory Skill.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return Skill(
      id: serializer.fromJson<String>(json['id']),
      name: serializer.fromJson<String>(json['name']),
      description: serializer.fromJson<String?>(json['description']),
      language: serializer.fromJson<String>(json['language']),
      identifySpeakers: serializer.fromJson<bool>(json['identifySpeakers']),
      vocabularyHints: serializer.fromJson<List<String>>(
        json['vocabularyHints'],
      ),
      outputType: serializer.fromJson<String>(json['outputType']),
      focusArea: serializer.fromJson<String?>(json['focusArea']),
      tone: serializer.fromJson<String>(json['tone']),
      outputLanguage: serializer.fromJson<String>(json['outputLanguage']),
      additionalInstructions: serializer.fromJson<String?>(
        json['additionalInstructions'],
      ),
      createdAt: serializer.fromJson<DateTime>(json['createdAt']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'id': serializer.toJson<String>(id),
      'name': serializer.toJson<String>(name),
      'description': serializer.toJson<String?>(description),
      'language': serializer.toJson<String>(language),
      'identifySpeakers': serializer.toJson<bool>(identifySpeakers),
      'vocabularyHints': serializer.toJson<List<String>>(vocabularyHints),
      'outputType': serializer.toJson<String>(outputType),
      'focusArea': serializer.toJson<String?>(focusArea),
      'tone': serializer.toJson<String>(tone),
      'outputLanguage': serializer.toJson<String>(outputLanguage),
      'additionalInstructions': serializer.toJson<String?>(
        additionalInstructions,
      ),
      'createdAt': serializer.toJson<DateTime>(createdAt),
    };
  }

  Skill copyWith({
    String? id,
    String? name,
    Value<String?> description = const Value.absent(),
    String? language,
    bool? identifySpeakers,
    List<String>? vocabularyHints,
    String? outputType,
    Value<String?> focusArea = const Value.absent(),
    String? tone,
    String? outputLanguage,
    Value<String?> additionalInstructions = const Value.absent(),
    DateTime? createdAt,
  }) => Skill(
    id: id ?? this.id,
    name: name ?? this.name,
    description: description.present ? description.value : this.description,
    language: language ?? this.language,
    identifySpeakers: identifySpeakers ?? this.identifySpeakers,
    vocabularyHints: vocabularyHints ?? this.vocabularyHints,
    outputType: outputType ?? this.outputType,
    focusArea: focusArea.present ? focusArea.value : this.focusArea,
    tone: tone ?? this.tone,
    outputLanguage: outputLanguage ?? this.outputLanguage,
    additionalInstructions: additionalInstructions.present
        ? additionalInstructions.value
        : this.additionalInstructions,
    createdAt: createdAt ?? this.createdAt,
  );
  Skill copyWithCompanion(SkillsCompanion data) {
    return Skill(
      id: data.id.present ? data.id.value : this.id,
      name: data.name.present ? data.name.value : this.name,
      description: data.description.present
          ? data.description.value
          : this.description,
      language: data.language.present ? data.language.value : this.language,
      identifySpeakers: data.identifySpeakers.present
          ? data.identifySpeakers.value
          : this.identifySpeakers,
      vocabularyHints: data.vocabularyHints.present
          ? data.vocabularyHints.value
          : this.vocabularyHints,
      outputType: data.outputType.present
          ? data.outputType.value
          : this.outputType,
      focusArea: data.focusArea.present ? data.focusArea.value : this.focusArea,
      tone: data.tone.present ? data.tone.value : this.tone,
      outputLanguage: data.outputLanguage.present
          ? data.outputLanguage.value
          : this.outputLanguage,
      additionalInstructions: data.additionalInstructions.present
          ? data.additionalInstructions.value
          : this.additionalInstructions,
      createdAt: data.createdAt.present ? data.createdAt.value : this.createdAt,
    );
  }

  @override
  String toString() {
    return (StringBuffer('Skill(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('description: $description, ')
          ..write('language: $language, ')
          ..write('identifySpeakers: $identifySpeakers, ')
          ..write('vocabularyHints: $vocabularyHints, ')
          ..write('outputType: $outputType, ')
          ..write('focusArea: $focusArea, ')
          ..write('tone: $tone, ')
          ..write('outputLanguage: $outputLanguage, ')
          ..write('additionalInstructions: $additionalInstructions, ')
          ..write('createdAt: $createdAt')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(
    id,
    name,
    description,
    language,
    identifySpeakers,
    vocabularyHints,
    outputType,
    focusArea,
    tone,
    outputLanguage,
    additionalInstructions,
    createdAt,
  );
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is Skill &&
          other.id == this.id &&
          other.name == this.name &&
          other.description == this.description &&
          other.language == this.language &&
          other.identifySpeakers == this.identifySpeakers &&
          other.vocabularyHints == this.vocabularyHints &&
          other.outputType == this.outputType &&
          other.focusArea == this.focusArea &&
          other.tone == this.tone &&
          other.outputLanguage == this.outputLanguage &&
          other.additionalInstructions == this.additionalInstructions &&
          other.createdAt == this.createdAt);
}

class SkillsCompanion extends UpdateCompanion<Skill> {
  final Value<String> id;
  final Value<String> name;
  final Value<String?> description;
  final Value<String> language;
  final Value<bool> identifySpeakers;
  final Value<List<String>> vocabularyHints;
  final Value<String> outputType;
  final Value<String?> focusArea;
  final Value<String> tone;
  final Value<String> outputLanguage;
  final Value<String?> additionalInstructions;
  final Value<DateTime> createdAt;
  final Value<int> rowid;
  const SkillsCompanion({
    this.id = const Value.absent(),
    this.name = const Value.absent(),
    this.description = const Value.absent(),
    this.language = const Value.absent(),
    this.identifySpeakers = const Value.absent(),
    this.vocabularyHints = const Value.absent(),
    this.outputType = const Value.absent(),
    this.focusArea = const Value.absent(),
    this.tone = const Value.absent(),
    this.outputLanguage = const Value.absent(),
    this.additionalInstructions = const Value.absent(),
    this.createdAt = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  SkillsCompanion.insert({
    required String id,
    required String name,
    this.description = const Value.absent(),
    this.language = const Value.absent(),
    this.identifySpeakers = const Value.absent(),
    this.vocabularyHints = const Value.absent(),
    this.outputType = const Value.absent(),
    this.focusArea = const Value.absent(),
    this.tone = const Value.absent(),
    this.outputLanguage = const Value.absent(),
    this.additionalInstructions = const Value.absent(),
    required DateTime createdAt,
    this.rowid = const Value.absent(),
  }) : id = Value(id),
       name = Value(name),
       createdAt = Value(createdAt);
  static Insertable<Skill> custom({
    Expression<String>? id,
    Expression<String>? name,
    Expression<String>? description,
    Expression<String>? language,
    Expression<bool>? identifySpeakers,
    Expression<String>? vocabularyHints,
    Expression<String>? outputType,
    Expression<String>? focusArea,
    Expression<String>? tone,
    Expression<String>? outputLanguage,
    Expression<String>? additionalInstructions,
    Expression<DateTime>? createdAt,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (id != null) 'id': id,
      if (name != null) 'name': name,
      if (description != null) 'description': description,
      if (language != null) 'language': language,
      if (identifySpeakers != null) 'identify_speakers': identifySpeakers,
      if (vocabularyHints != null) 'vocabulary_hints': vocabularyHints,
      if (outputType != null) 'output_type': outputType,
      if (focusArea != null) 'focus_area': focusArea,
      if (tone != null) 'tone': tone,
      if (outputLanguage != null) 'output_language': outputLanguage,
      if (additionalInstructions != null)
        'additional_instructions': additionalInstructions,
      if (createdAt != null) 'created_at': createdAt,
      if (rowid != null) 'rowid': rowid,
    });
  }

  SkillsCompanion copyWith({
    Value<String>? id,
    Value<String>? name,
    Value<String?>? description,
    Value<String>? language,
    Value<bool>? identifySpeakers,
    Value<List<String>>? vocabularyHints,
    Value<String>? outputType,
    Value<String?>? focusArea,
    Value<String>? tone,
    Value<String>? outputLanguage,
    Value<String?>? additionalInstructions,
    Value<DateTime>? createdAt,
    Value<int>? rowid,
  }) {
    return SkillsCompanion(
      id: id ?? this.id,
      name: name ?? this.name,
      description: description ?? this.description,
      language: language ?? this.language,
      identifySpeakers: identifySpeakers ?? this.identifySpeakers,
      vocabularyHints: vocabularyHints ?? this.vocabularyHints,
      outputType: outputType ?? this.outputType,
      focusArea: focusArea ?? this.focusArea,
      tone: tone ?? this.tone,
      outputLanguage: outputLanguage ?? this.outputLanguage,
      additionalInstructions:
          additionalInstructions ?? this.additionalInstructions,
      createdAt: createdAt ?? this.createdAt,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (id.present) {
      map['id'] = Variable<String>(id.value);
    }
    if (name.present) {
      map['name'] = Variable<String>(name.value);
    }
    if (description.present) {
      map['description'] = Variable<String>(description.value);
    }
    if (language.present) {
      map['language'] = Variable<String>(language.value);
    }
    if (identifySpeakers.present) {
      map['identify_speakers'] = Variable<bool>(identifySpeakers.value);
    }
    if (vocabularyHints.present) {
      map['vocabulary_hints'] = Variable<String>(
        $SkillsTable.$convertervocabularyHints.toSql(vocabularyHints.value),
      );
    }
    if (outputType.present) {
      map['output_type'] = Variable<String>(outputType.value);
    }
    if (focusArea.present) {
      map['focus_area'] = Variable<String>(focusArea.value);
    }
    if (tone.present) {
      map['tone'] = Variable<String>(tone.value);
    }
    if (outputLanguage.present) {
      map['output_language'] = Variable<String>(outputLanguage.value);
    }
    if (additionalInstructions.present) {
      map['additional_instructions'] = Variable<String>(
        additionalInstructions.value,
      );
    }
    if (createdAt.present) {
      map['created_at'] = Variable<DateTime>(createdAt.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('SkillsCompanion(')
          ..write('id: $id, ')
          ..write('name: $name, ')
          ..write('description: $description, ')
          ..write('language: $language, ')
          ..write('identifySpeakers: $identifySpeakers, ')
          ..write('vocabularyHints: $vocabularyHints, ')
          ..write('outputType: $outputType, ')
          ..write('focusArea: $focusArea, ')
          ..write('tone: $tone, ')
          ..write('outputLanguage: $outputLanguage, ')
          ..write('additionalInstructions: $additionalInstructions, ')
          ..write('createdAt: $createdAt, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

class $ModeSkillsTable extends ModeSkills
    with TableInfo<$ModeSkillsTable, ModeSkill> {
  @override
  final GeneratedDatabase attachedDatabase;
  final String? _alias;
  $ModeSkillsTable(this.attachedDatabase, [this._alias]);
  static const VerificationMeta _modeIdMeta = const VerificationMeta('modeId');
  @override
  late final GeneratedColumn<String> modeId = GeneratedColumn<String>(
    'mode_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _skillIdMeta = const VerificationMeta(
    'skillId',
  );
  @override
  late final GeneratedColumn<String> skillId = GeneratedColumn<String>(
    'skill_id',
    aliasedName,
    false,
    type: DriftSqlType.string,
    requiredDuringInsert: true,
  );
  static const VerificationMeta _sortOrderMeta = const VerificationMeta(
    'sortOrder',
  );
  @override
  late final GeneratedColumn<int> sortOrder = GeneratedColumn<int>(
    'sort_order',
    aliasedName,
    false,
    type: DriftSqlType.int,
    requiredDuringInsert: true,
  );
  @override
  List<GeneratedColumn> get $columns => [modeId, skillId, sortOrder];
  @override
  String get aliasedName => _alias ?? actualTableName;
  @override
  String get actualTableName => $name;
  static const String $name = 'mode_skills';
  @override
  VerificationContext validateIntegrity(
    Insertable<ModeSkill> instance, {
    bool isInserting = false,
  }) {
    final context = VerificationContext();
    final data = instance.toColumns(true);
    if (data.containsKey('mode_id')) {
      context.handle(
        _modeIdMeta,
        modeId.isAcceptableOrUnknown(data['mode_id']!, _modeIdMeta),
      );
    } else if (isInserting) {
      context.missing(_modeIdMeta);
    }
    if (data.containsKey('skill_id')) {
      context.handle(
        _skillIdMeta,
        skillId.isAcceptableOrUnknown(data['skill_id']!, _skillIdMeta),
      );
    } else if (isInserting) {
      context.missing(_skillIdMeta);
    }
    if (data.containsKey('sort_order')) {
      context.handle(
        _sortOrderMeta,
        sortOrder.isAcceptableOrUnknown(data['sort_order']!, _sortOrderMeta),
      );
    } else if (isInserting) {
      context.missing(_sortOrderMeta);
    }
    return context;
  }

  @override
  Set<GeneratedColumn> get $primaryKey => {modeId, skillId};
  @override
  ModeSkill map(Map<String, dynamic> data, {String? tablePrefix}) {
    final effectivePrefix = tablePrefix != null ? '$tablePrefix.' : '';
    return ModeSkill(
      modeId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}mode_id'],
      )!,
      skillId: attachedDatabase.typeMapping.read(
        DriftSqlType.string,
        data['${effectivePrefix}skill_id'],
      )!,
      sortOrder: attachedDatabase.typeMapping.read(
        DriftSqlType.int,
        data['${effectivePrefix}sort_order'],
      )!,
    );
  }

  @override
  $ModeSkillsTable createAlias(String alias) {
    return $ModeSkillsTable(attachedDatabase, alias);
  }
}

class ModeSkill extends DataClass implements Insertable<ModeSkill> {
  final String modeId;
  final String skillId;
  final int sortOrder;
  const ModeSkill({
    required this.modeId,
    required this.skillId,
    required this.sortOrder,
  });
  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    map['mode_id'] = Variable<String>(modeId);
    map['skill_id'] = Variable<String>(skillId);
    map['sort_order'] = Variable<int>(sortOrder);
    return map;
  }

  ModeSkillsCompanion toCompanion(bool nullToAbsent) {
    return ModeSkillsCompanion(
      modeId: Value(modeId),
      skillId: Value(skillId),
      sortOrder: Value(sortOrder),
    );
  }

  factory ModeSkill.fromJson(
    Map<String, dynamic> json, {
    ValueSerializer? serializer,
  }) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return ModeSkill(
      modeId: serializer.fromJson<String>(json['modeId']),
      skillId: serializer.fromJson<String>(json['skillId']),
      sortOrder: serializer.fromJson<int>(json['sortOrder']),
    );
  }
  @override
  Map<String, dynamic> toJson({ValueSerializer? serializer}) {
    serializer ??= driftRuntimeOptions.defaultSerializer;
    return <String, dynamic>{
      'modeId': serializer.toJson<String>(modeId),
      'skillId': serializer.toJson<String>(skillId),
      'sortOrder': serializer.toJson<int>(sortOrder),
    };
  }

  ModeSkill copyWith({String? modeId, String? skillId, int? sortOrder}) =>
      ModeSkill(
        modeId: modeId ?? this.modeId,
        skillId: skillId ?? this.skillId,
        sortOrder: sortOrder ?? this.sortOrder,
      );
  ModeSkill copyWithCompanion(ModeSkillsCompanion data) {
    return ModeSkill(
      modeId: data.modeId.present ? data.modeId.value : this.modeId,
      skillId: data.skillId.present ? data.skillId.value : this.skillId,
      sortOrder: data.sortOrder.present ? data.sortOrder.value : this.sortOrder,
    );
  }

  @override
  String toString() {
    return (StringBuffer('ModeSkill(')
          ..write('modeId: $modeId, ')
          ..write('skillId: $skillId, ')
          ..write('sortOrder: $sortOrder')
          ..write(')'))
        .toString();
  }

  @override
  int get hashCode => Object.hash(modeId, skillId, sortOrder);
  @override
  bool operator ==(Object other) =>
      identical(this, other) ||
      (other is ModeSkill &&
          other.modeId == this.modeId &&
          other.skillId == this.skillId &&
          other.sortOrder == this.sortOrder);
}

class ModeSkillsCompanion extends UpdateCompanion<ModeSkill> {
  final Value<String> modeId;
  final Value<String> skillId;
  final Value<int> sortOrder;
  final Value<int> rowid;
  const ModeSkillsCompanion({
    this.modeId = const Value.absent(),
    this.skillId = const Value.absent(),
    this.sortOrder = const Value.absent(),
    this.rowid = const Value.absent(),
  });
  ModeSkillsCompanion.insert({
    required String modeId,
    required String skillId,
    required int sortOrder,
    this.rowid = const Value.absent(),
  }) : modeId = Value(modeId),
       skillId = Value(skillId),
       sortOrder = Value(sortOrder);
  static Insertable<ModeSkill> custom({
    Expression<String>? modeId,
    Expression<String>? skillId,
    Expression<int>? sortOrder,
    Expression<int>? rowid,
  }) {
    return RawValuesInsertable({
      if (modeId != null) 'mode_id': modeId,
      if (skillId != null) 'skill_id': skillId,
      if (sortOrder != null) 'sort_order': sortOrder,
      if (rowid != null) 'rowid': rowid,
    });
  }

  ModeSkillsCompanion copyWith({
    Value<String>? modeId,
    Value<String>? skillId,
    Value<int>? sortOrder,
    Value<int>? rowid,
  }) {
    return ModeSkillsCompanion(
      modeId: modeId ?? this.modeId,
      skillId: skillId ?? this.skillId,
      sortOrder: sortOrder ?? this.sortOrder,
      rowid: rowid ?? this.rowid,
    );
  }

  @override
  Map<String, Expression> toColumns(bool nullToAbsent) {
    final map = <String, Expression>{};
    if (modeId.present) {
      map['mode_id'] = Variable<String>(modeId.value);
    }
    if (skillId.present) {
      map['skill_id'] = Variable<String>(skillId.value);
    }
    if (sortOrder.present) {
      map['sort_order'] = Variable<int>(sortOrder.value);
    }
    if (rowid.present) {
      map['rowid'] = Variable<int>(rowid.value);
    }
    return map;
  }

  @override
  String toString() {
    return (StringBuffer('ModeSkillsCompanion(')
          ..write('modeId: $modeId, ')
          ..write('skillId: $skillId, ')
          ..write('sortOrder: $sortOrder, ')
          ..write('rowid: $rowid')
          ..write(')'))
        .toString();
  }
}

abstract class _$AppDatabase extends GeneratedDatabase {
  _$AppDatabase(QueryExecutor e) : super(e);
  $AppDatabaseManager get managers => $AppDatabaseManager(this);
  late final $RecordingsTable recordings = $RecordingsTable(this);
  late final $ModesTable modes = $ModesTable(this);
  late final $SkillsTable skills = $SkillsTable(this);
  late final $ModeSkillsTable modeSkills = $ModeSkillsTable(this);
  late final RecordingDao recordingDao = RecordingDao(this as AppDatabase);
  late final ModeDao modeDao = ModeDao(this as AppDatabase);
  late final SkillDao skillDao = SkillDao(this as AppDatabase);
  @override
  Iterable<TableInfo<Table, Object?>> get allTables =>
      allSchemaEntities.whereType<TableInfo<Table, Object?>>();
  @override
  List<DatabaseSchemaEntity> get allSchemaEntities => [
    recordings,
    modes,
    skills,
    modeSkills,
  ];
}

typedef $$RecordingsTableCreateCompanionBuilder =
    RecordingsCompanion Function({
      required String id,
      required String title,
      Value<String?> memo,
      Value<List<String>> tags,
      Value<String?> category,
      Value<String> language,
      Value<String?> modeId,
      required String audioFilePath,
      Value<int?> audioDurationMs,
      Value<int?> audioFileSize,
      Value<String> uploadStatus,
      Value<String?> driveFileId,
      Value<String?> jobId,
      Value<String> jobStatus,
      Value<String?> jobError,
      required DateTime createdAt,
      required DateTime updatedAt,
      Value<int> rowid,
    });
typedef $$RecordingsTableUpdateCompanionBuilder =
    RecordingsCompanion Function({
      Value<String> id,
      Value<String> title,
      Value<String?> memo,
      Value<List<String>> tags,
      Value<String?> category,
      Value<String> language,
      Value<String?> modeId,
      Value<String> audioFilePath,
      Value<int?> audioDurationMs,
      Value<int?> audioFileSize,
      Value<String> uploadStatus,
      Value<String?> driveFileId,
      Value<String?> jobId,
      Value<String> jobStatus,
      Value<String?> jobError,
      Value<DateTime> createdAt,
      Value<DateTime> updatedAt,
      Value<int> rowid,
    });

class $$RecordingsTableFilterComposer
    extends Composer<_$AppDatabase, $RecordingsTable> {
  $$RecordingsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get title => $composableBuilder(
    column: $table.title,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get memo => $composableBuilder(
    column: $table.memo,
    builder: (column) => ColumnFilters(column),
  );

  ColumnWithTypeConverterFilters<List<String>, List<String>, String> get tags =>
      $composableBuilder(
        column: $table.tags,
        builder: (column) => ColumnWithTypeConverterFilters(column),
      );

  ColumnFilters<String> get category => $composableBuilder(
    column: $table.category,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get language => $composableBuilder(
    column: $table.language,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get modeId => $composableBuilder(
    column: $table.modeId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get audioFilePath => $composableBuilder(
    column: $table.audioFilePath,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get audioDurationMs => $composableBuilder(
    column: $table.audioDurationMs,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get audioFileSize => $composableBuilder(
    column: $table.audioFileSize,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get uploadStatus => $composableBuilder(
    column: $table.uploadStatus,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get driveFileId => $composableBuilder(
    column: $table.driveFileId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get jobId => $composableBuilder(
    column: $table.jobId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get jobStatus => $composableBuilder(
    column: $table.jobStatus,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get jobError => $composableBuilder(
    column: $table.jobError,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$RecordingsTableOrderingComposer
    extends Composer<_$AppDatabase, $RecordingsTable> {
  $$RecordingsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get title => $composableBuilder(
    column: $table.title,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get memo => $composableBuilder(
    column: $table.memo,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get tags => $composableBuilder(
    column: $table.tags,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get category => $composableBuilder(
    column: $table.category,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get language => $composableBuilder(
    column: $table.language,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get modeId => $composableBuilder(
    column: $table.modeId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get audioFilePath => $composableBuilder(
    column: $table.audioFilePath,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get audioDurationMs => $composableBuilder(
    column: $table.audioDurationMs,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get audioFileSize => $composableBuilder(
    column: $table.audioFileSize,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get uploadStatus => $composableBuilder(
    column: $table.uploadStatus,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get driveFileId => $composableBuilder(
    column: $table.driveFileId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get jobId => $composableBuilder(
    column: $table.jobId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get jobStatus => $composableBuilder(
    column: $table.jobStatus,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get jobError => $composableBuilder(
    column: $table.jobError,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get updatedAt => $composableBuilder(
    column: $table.updatedAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$RecordingsTableAnnotationComposer
    extends Composer<_$AppDatabase, $RecordingsTable> {
  $$RecordingsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get title =>
      $composableBuilder(column: $table.title, builder: (column) => column);

  GeneratedColumn<String> get memo =>
      $composableBuilder(column: $table.memo, builder: (column) => column);

  GeneratedColumnWithTypeConverter<List<String>, String> get tags =>
      $composableBuilder(column: $table.tags, builder: (column) => column);

  GeneratedColumn<String> get category =>
      $composableBuilder(column: $table.category, builder: (column) => column);

  GeneratedColumn<String> get language =>
      $composableBuilder(column: $table.language, builder: (column) => column);

  GeneratedColumn<String> get modeId =>
      $composableBuilder(column: $table.modeId, builder: (column) => column);

  GeneratedColumn<String> get audioFilePath => $composableBuilder(
    column: $table.audioFilePath,
    builder: (column) => column,
  );

  GeneratedColumn<int> get audioDurationMs => $composableBuilder(
    column: $table.audioDurationMs,
    builder: (column) => column,
  );

  GeneratedColumn<int> get audioFileSize => $composableBuilder(
    column: $table.audioFileSize,
    builder: (column) => column,
  );

  GeneratedColumn<String> get uploadStatus => $composableBuilder(
    column: $table.uploadStatus,
    builder: (column) => column,
  );

  GeneratedColumn<String> get driveFileId => $composableBuilder(
    column: $table.driveFileId,
    builder: (column) => column,
  );

  GeneratedColumn<String> get jobId =>
      $composableBuilder(column: $table.jobId, builder: (column) => column);

  GeneratedColumn<String> get jobStatus =>
      $composableBuilder(column: $table.jobStatus, builder: (column) => column);

  GeneratedColumn<String> get jobError =>
      $composableBuilder(column: $table.jobError, builder: (column) => column);

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);

  GeneratedColumn<DateTime> get updatedAt =>
      $composableBuilder(column: $table.updatedAt, builder: (column) => column);
}

class $$RecordingsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $RecordingsTable,
          Recording,
          $$RecordingsTableFilterComposer,
          $$RecordingsTableOrderingComposer,
          $$RecordingsTableAnnotationComposer,
          $$RecordingsTableCreateCompanionBuilder,
          $$RecordingsTableUpdateCompanionBuilder,
          (
            Recording,
            BaseReferences<_$AppDatabase, $RecordingsTable, Recording>,
          ),
          Recording,
          PrefetchHooks Function()
        > {
  $$RecordingsTableTableManager(_$AppDatabase db, $RecordingsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$RecordingsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$RecordingsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$RecordingsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String> title = const Value.absent(),
                Value<String?> memo = const Value.absent(),
                Value<List<String>> tags = const Value.absent(),
                Value<String?> category = const Value.absent(),
                Value<String> language = const Value.absent(),
                Value<String?> modeId = const Value.absent(),
                Value<String> audioFilePath = const Value.absent(),
                Value<int?> audioDurationMs = const Value.absent(),
                Value<int?> audioFileSize = const Value.absent(),
                Value<String> uploadStatus = const Value.absent(),
                Value<String?> driveFileId = const Value.absent(),
                Value<String?> jobId = const Value.absent(),
                Value<String> jobStatus = const Value.absent(),
                Value<String?> jobError = const Value.absent(),
                Value<DateTime> createdAt = const Value.absent(),
                Value<DateTime> updatedAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => RecordingsCompanion(
                id: id,
                title: title,
                memo: memo,
                tags: tags,
                category: category,
                language: language,
                modeId: modeId,
                audioFilePath: audioFilePath,
                audioDurationMs: audioDurationMs,
                audioFileSize: audioFileSize,
                uploadStatus: uploadStatus,
                driveFileId: driveFileId,
                jobId: jobId,
                jobStatus: jobStatus,
                jobError: jobError,
                createdAt: createdAt,
                updatedAt: updatedAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                required String title,
                Value<String?> memo = const Value.absent(),
                Value<List<String>> tags = const Value.absent(),
                Value<String?> category = const Value.absent(),
                Value<String> language = const Value.absent(),
                Value<String?> modeId = const Value.absent(),
                required String audioFilePath,
                Value<int?> audioDurationMs = const Value.absent(),
                Value<int?> audioFileSize = const Value.absent(),
                Value<String> uploadStatus = const Value.absent(),
                Value<String?> driveFileId = const Value.absent(),
                Value<String?> jobId = const Value.absent(),
                Value<String> jobStatus = const Value.absent(),
                Value<String?> jobError = const Value.absent(),
                required DateTime createdAt,
                required DateTime updatedAt,
                Value<int> rowid = const Value.absent(),
              }) => RecordingsCompanion.insert(
                id: id,
                title: title,
                memo: memo,
                tags: tags,
                category: category,
                language: language,
                modeId: modeId,
                audioFilePath: audioFilePath,
                audioDurationMs: audioDurationMs,
                audioFileSize: audioFileSize,
                uploadStatus: uploadStatus,
                driveFileId: driveFileId,
                jobId: jobId,
                jobStatus: jobStatus,
                jobError: jobError,
                createdAt: createdAt,
                updatedAt: updatedAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$RecordingsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $RecordingsTable,
      Recording,
      $$RecordingsTableFilterComposer,
      $$RecordingsTableOrderingComposer,
      $$RecordingsTableAnnotationComposer,
      $$RecordingsTableCreateCompanionBuilder,
      $$RecordingsTableUpdateCompanionBuilder,
      (Recording, BaseReferences<_$AppDatabase, $RecordingsTable, Recording>),
      Recording,
      PrefetchHooks Function()
    >;
typedef $$ModesTableCreateCompanionBuilder =
    ModesCompanion Function({
      required String id,
      required String name,
      required String icon,
      Value<bool> isDefault,
      Value<bool> isSeeded,
      required DateTime createdAt,
      Value<int> rowid,
    });
typedef $$ModesTableUpdateCompanionBuilder =
    ModesCompanion Function({
      Value<String> id,
      Value<String> name,
      Value<String> icon,
      Value<bool> isDefault,
      Value<bool> isSeeded,
      Value<DateTime> createdAt,
      Value<int> rowid,
    });

class $$ModesTableFilterComposer extends Composer<_$AppDatabase, $ModesTable> {
  $$ModesTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get icon => $composableBuilder(
    column: $table.icon,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get isDefault => $composableBuilder(
    column: $table.isDefault,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get isSeeded => $composableBuilder(
    column: $table.isSeeded,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$ModesTableOrderingComposer
    extends Composer<_$AppDatabase, $ModesTable> {
  $$ModesTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get icon => $composableBuilder(
    column: $table.icon,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get isDefault => $composableBuilder(
    column: $table.isDefault,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get isSeeded => $composableBuilder(
    column: $table.isSeeded,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$ModesTableAnnotationComposer
    extends Composer<_$AppDatabase, $ModesTable> {
  $$ModesTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get icon =>
      $composableBuilder(column: $table.icon, builder: (column) => column);

  GeneratedColumn<bool> get isDefault =>
      $composableBuilder(column: $table.isDefault, builder: (column) => column);

  GeneratedColumn<bool> get isSeeded =>
      $composableBuilder(column: $table.isSeeded, builder: (column) => column);

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);
}

class $$ModesTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $ModesTable,
          Mode,
          $$ModesTableFilterComposer,
          $$ModesTableOrderingComposer,
          $$ModesTableAnnotationComposer,
          $$ModesTableCreateCompanionBuilder,
          $$ModesTableUpdateCompanionBuilder,
          (Mode, BaseReferences<_$AppDatabase, $ModesTable, Mode>),
          Mode,
          PrefetchHooks Function()
        > {
  $$ModesTableTableManager(_$AppDatabase db, $ModesTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ModesTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ModesTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ModesTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String> name = const Value.absent(),
                Value<String> icon = const Value.absent(),
                Value<bool> isDefault = const Value.absent(),
                Value<bool> isSeeded = const Value.absent(),
                Value<DateTime> createdAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => ModesCompanion(
                id: id,
                name: name,
                icon: icon,
                isDefault: isDefault,
                isSeeded: isSeeded,
                createdAt: createdAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                required String name,
                required String icon,
                Value<bool> isDefault = const Value.absent(),
                Value<bool> isSeeded = const Value.absent(),
                required DateTime createdAt,
                Value<int> rowid = const Value.absent(),
              }) => ModesCompanion.insert(
                id: id,
                name: name,
                icon: icon,
                isDefault: isDefault,
                isSeeded: isSeeded,
                createdAt: createdAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$ModesTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $ModesTable,
      Mode,
      $$ModesTableFilterComposer,
      $$ModesTableOrderingComposer,
      $$ModesTableAnnotationComposer,
      $$ModesTableCreateCompanionBuilder,
      $$ModesTableUpdateCompanionBuilder,
      (Mode, BaseReferences<_$AppDatabase, $ModesTable, Mode>),
      Mode,
      PrefetchHooks Function()
    >;
typedef $$SkillsTableCreateCompanionBuilder =
    SkillsCompanion Function({
      required String id,
      required String name,
      Value<String?> description,
      Value<String> language,
      Value<bool> identifySpeakers,
      Value<List<String>> vocabularyHints,
      Value<String> outputType,
      Value<String?> focusArea,
      Value<String> tone,
      Value<String> outputLanguage,
      Value<String?> additionalInstructions,
      required DateTime createdAt,
      Value<int> rowid,
    });
typedef $$SkillsTableUpdateCompanionBuilder =
    SkillsCompanion Function({
      Value<String> id,
      Value<String> name,
      Value<String?> description,
      Value<String> language,
      Value<bool> identifySpeakers,
      Value<List<String>> vocabularyHints,
      Value<String> outputType,
      Value<String?> focusArea,
      Value<String> tone,
      Value<String> outputLanguage,
      Value<String?> additionalInstructions,
      Value<DateTime> createdAt,
      Value<int> rowid,
    });

class $$SkillsTableFilterComposer
    extends Composer<_$AppDatabase, $SkillsTable> {
  $$SkillsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get description => $composableBuilder(
    column: $table.description,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get language => $composableBuilder(
    column: $table.language,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<bool> get identifySpeakers => $composableBuilder(
    column: $table.identifySpeakers,
    builder: (column) => ColumnFilters(column),
  );

  ColumnWithTypeConverterFilters<List<String>, List<String>, String>
  get vocabularyHints => $composableBuilder(
    column: $table.vocabularyHints,
    builder: (column) => ColumnWithTypeConverterFilters(column),
  );

  ColumnFilters<String> get outputType => $composableBuilder(
    column: $table.outputType,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get focusArea => $composableBuilder(
    column: $table.focusArea,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get tone => $composableBuilder(
    column: $table.tone,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get outputLanguage => $composableBuilder(
    column: $table.outputLanguage,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get additionalInstructions => $composableBuilder(
    column: $table.additionalInstructions,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnFilters(column),
  );
}

class $$SkillsTableOrderingComposer
    extends Composer<_$AppDatabase, $SkillsTable> {
  $$SkillsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get id => $composableBuilder(
    column: $table.id,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get name => $composableBuilder(
    column: $table.name,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get description => $composableBuilder(
    column: $table.description,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get language => $composableBuilder(
    column: $table.language,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<bool> get identifySpeakers => $composableBuilder(
    column: $table.identifySpeakers,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get vocabularyHints => $composableBuilder(
    column: $table.vocabularyHints,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get outputType => $composableBuilder(
    column: $table.outputType,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get focusArea => $composableBuilder(
    column: $table.focusArea,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get tone => $composableBuilder(
    column: $table.tone,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get outputLanguage => $composableBuilder(
    column: $table.outputLanguage,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get additionalInstructions => $composableBuilder(
    column: $table.additionalInstructions,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<DateTime> get createdAt => $composableBuilder(
    column: $table.createdAt,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$SkillsTableAnnotationComposer
    extends Composer<_$AppDatabase, $SkillsTable> {
  $$SkillsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get id =>
      $composableBuilder(column: $table.id, builder: (column) => column);

  GeneratedColumn<String> get name =>
      $composableBuilder(column: $table.name, builder: (column) => column);

  GeneratedColumn<String> get description => $composableBuilder(
    column: $table.description,
    builder: (column) => column,
  );

  GeneratedColumn<String> get language =>
      $composableBuilder(column: $table.language, builder: (column) => column);

  GeneratedColumn<bool> get identifySpeakers => $composableBuilder(
    column: $table.identifySpeakers,
    builder: (column) => column,
  );

  GeneratedColumnWithTypeConverter<List<String>, String> get vocabularyHints =>
      $composableBuilder(
        column: $table.vocabularyHints,
        builder: (column) => column,
      );

  GeneratedColumn<String> get outputType => $composableBuilder(
    column: $table.outputType,
    builder: (column) => column,
  );

  GeneratedColumn<String> get focusArea =>
      $composableBuilder(column: $table.focusArea, builder: (column) => column);

  GeneratedColumn<String> get tone =>
      $composableBuilder(column: $table.tone, builder: (column) => column);

  GeneratedColumn<String> get outputLanguage => $composableBuilder(
    column: $table.outputLanguage,
    builder: (column) => column,
  );

  GeneratedColumn<String> get additionalInstructions => $composableBuilder(
    column: $table.additionalInstructions,
    builder: (column) => column,
  );

  GeneratedColumn<DateTime> get createdAt =>
      $composableBuilder(column: $table.createdAt, builder: (column) => column);
}

class $$SkillsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $SkillsTable,
          Skill,
          $$SkillsTableFilterComposer,
          $$SkillsTableOrderingComposer,
          $$SkillsTableAnnotationComposer,
          $$SkillsTableCreateCompanionBuilder,
          $$SkillsTableUpdateCompanionBuilder,
          (Skill, BaseReferences<_$AppDatabase, $SkillsTable, Skill>),
          Skill,
          PrefetchHooks Function()
        > {
  $$SkillsTableTableManager(_$AppDatabase db, $SkillsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$SkillsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$SkillsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$SkillsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> id = const Value.absent(),
                Value<String> name = const Value.absent(),
                Value<String?> description = const Value.absent(),
                Value<String> language = const Value.absent(),
                Value<bool> identifySpeakers = const Value.absent(),
                Value<List<String>> vocabularyHints = const Value.absent(),
                Value<String> outputType = const Value.absent(),
                Value<String?> focusArea = const Value.absent(),
                Value<String> tone = const Value.absent(),
                Value<String> outputLanguage = const Value.absent(),
                Value<String?> additionalInstructions = const Value.absent(),
                Value<DateTime> createdAt = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => SkillsCompanion(
                id: id,
                name: name,
                description: description,
                language: language,
                identifySpeakers: identifySpeakers,
                vocabularyHints: vocabularyHints,
                outputType: outputType,
                focusArea: focusArea,
                tone: tone,
                outputLanguage: outputLanguage,
                additionalInstructions: additionalInstructions,
                createdAt: createdAt,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String id,
                required String name,
                Value<String?> description = const Value.absent(),
                Value<String> language = const Value.absent(),
                Value<bool> identifySpeakers = const Value.absent(),
                Value<List<String>> vocabularyHints = const Value.absent(),
                Value<String> outputType = const Value.absent(),
                Value<String?> focusArea = const Value.absent(),
                Value<String> tone = const Value.absent(),
                Value<String> outputLanguage = const Value.absent(),
                Value<String?> additionalInstructions = const Value.absent(),
                required DateTime createdAt,
                Value<int> rowid = const Value.absent(),
              }) => SkillsCompanion.insert(
                id: id,
                name: name,
                description: description,
                language: language,
                identifySpeakers: identifySpeakers,
                vocabularyHints: vocabularyHints,
                outputType: outputType,
                focusArea: focusArea,
                tone: tone,
                outputLanguage: outputLanguage,
                additionalInstructions: additionalInstructions,
                createdAt: createdAt,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$SkillsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $SkillsTable,
      Skill,
      $$SkillsTableFilterComposer,
      $$SkillsTableOrderingComposer,
      $$SkillsTableAnnotationComposer,
      $$SkillsTableCreateCompanionBuilder,
      $$SkillsTableUpdateCompanionBuilder,
      (Skill, BaseReferences<_$AppDatabase, $SkillsTable, Skill>),
      Skill,
      PrefetchHooks Function()
    >;
typedef $$ModeSkillsTableCreateCompanionBuilder =
    ModeSkillsCompanion Function({
      required String modeId,
      required String skillId,
      required int sortOrder,
      Value<int> rowid,
    });
typedef $$ModeSkillsTableUpdateCompanionBuilder =
    ModeSkillsCompanion Function({
      Value<String> modeId,
      Value<String> skillId,
      Value<int> sortOrder,
      Value<int> rowid,
    });

class $$ModeSkillsTableFilterComposer
    extends Composer<_$AppDatabase, $ModeSkillsTable> {
  $$ModeSkillsTableFilterComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnFilters<String> get modeId => $composableBuilder(
    column: $table.modeId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<String> get skillId => $composableBuilder(
    column: $table.skillId,
    builder: (column) => ColumnFilters(column),
  );

  ColumnFilters<int> get sortOrder => $composableBuilder(
    column: $table.sortOrder,
    builder: (column) => ColumnFilters(column),
  );
}

class $$ModeSkillsTableOrderingComposer
    extends Composer<_$AppDatabase, $ModeSkillsTable> {
  $$ModeSkillsTableOrderingComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  ColumnOrderings<String> get modeId => $composableBuilder(
    column: $table.modeId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<String> get skillId => $composableBuilder(
    column: $table.skillId,
    builder: (column) => ColumnOrderings(column),
  );

  ColumnOrderings<int> get sortOrder => $composableBuilder(
    column: $table.sortOrder,
    builder: (column) => ColumnOrderings(column),
  );
}

class $$ModeSkillsTableAnnotationComposer
    extends Composer<_$AppDatabase, $ModeSkillsTable> {
  $$ModeSkillsTableAnnotationComposer({
    required super.$db,
    required super.$table,
    super.joinBuilder,
    super.$addJoinBuilderToRootComposer,
    super.$removeJoinBuilderFromRootComposer,
  });
  GeneratedColumn<String> get modeId =>
      $composableBuilder(column: $table.modeId, builder: (column) => column);

  GeneratedColumn<String> get skillId =>
      $composableBuilder(column: $table.skillId, builder: (column) => column);

  GeneratedColumn<int> get sortOrder =>
      $composableBuilder(column: $table.sortOrder, builder: (column) => column);
}

class $$ModeSkillsTableTableManager
    extends
        RootTableManager<
          _$AppDatabase,
          $ModeSkillsTable,
          ModeSkill,
          $$ModeSkillsTableFilterComposer,
          $$ModeSkillsTableOrderingComposer,
          $$ModeSkillsTableAnnotationComposer,
          $$ModeSkillsTableCreateCompanionBuilder,
          $$ModeSkillsTableUpdateCompanionBuilder,
          (
            ModeSkill,
            BaseReferences<_$AppDatabase, $ModeSkillsTable, ModeSkill>,
          ),
          ModeSkill,
          PrefetchHooks Function()
        > {
  $$ModeSkillsTableTableManager(_$AppDatabase db, $ModeSkillsTable table)
    : super(
        TableManagerState(
          db: db,
          table: table,
          createFilteringComposer: () =>
              $$ModeSkillsTableFilterComposer($db: db, $table: table),
          createOrderingComposer: () =>
              $$ModeSkillsTableOrderingComposer($db: db, $table: table),
          createComputedFieldComposer: () =>
              $$ModeSkillsTableAnnotationComposer($db: db, $table: table),
          updateCompanionCallback:
              ({
                Value<String> modeId = const Value.absent(),
                Value<String> skillId = const Value.absent(),
                Value<int> sortOrder = const Value.absent(),
                Value<int> rowid = const Value.absent(),
              }) => ModeSkillsCompanion(
                modeId: modeId,
                skillId: skillId,
                sortOrder: sortOrder,
                rowid: rowid,
              ),
          createCompanionCallback:
              ({
                required String modeId,
                required String skillId,
                required int sortOrder,
                Value<int> rowid = const Value.absent(),
              }) => ModeSkillsCompanion.insert(
                modeId: modeId,
                skillId: skillId,
                sortOrder: sortOrder,
                rowid: rowid,
              ),
          withReferenceMapper: (p0) => p0
              .map((e) => (e.readTable(table), BaseReferences(db, table, e)))
              .toList(),
          prefetchHooksCallback: null,
        ),
      );
}

typedef $$ModeSkillsTableProcessedTableManager =
    ProcessedTableManager<
      _$AppDatabase,
      $ModeSkillsTable,
      ModeSkill,
      $$ModeSkillsTableFilterComposer,
      $$ModeSkillsTableOrderingComposer,
      $$ModeSkillsTableAnnotationComposer,
      $$ModeSkillsTableCreateCompanionBuilder,
      $$ModeSkillsTableUpdateCompanionBuilder,
      (ModeSkill, BaseReferences<_$AppDatabase, $ModeSkillsTable, ModeSkill>),
      ModeSkill,
      PrefetchHooks Function()
    >;

class $AppDatabaseManager {
  final _$AppDatabase _db;
  $AppDatabaseManager(this._db);
  $$RecordingsTableTableManager get recordings =>
      $$RecordingsTableTableManager(_db, _db.recordings);
  $$ModesTableTableManager get modes =>
      $$ModesTableTableManager(_db, _db.modes);
  $$SkillsTableTableManager get skills =>
      $$SkillsTableTableManager(_db, _db.skills);
  $$ModeSkillsTableTableManager get modeSkills =>
      $$ModeSkillsTableTableManager(_db, _db.modeSkills);
}
