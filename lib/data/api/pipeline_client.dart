import 'dart:convert';
import 'package:http/http.dart' as http;

// Override at build time with --dart-define=PIPELINE_URL=https://your-server.example.com
const String _baseUrl = String.fromEnvironment(
  'PIPELINE_URL',
  defaultValue: 'http://localhost:8000',
);

class PipelineClient {
  PipelineClient({http.Client? client}) : _client = client ?? http.Client();

  final http.Client _client;

  Future<void> resolveCheckpoint(String jobId, {required bool skipped}) async {
    final uri = Uri.parse('$_baseUrl/jobs/$jobId/checkpoint');
    final response = await _client.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({'data': if (skipped) {'skipped': true} else {}}),
    );
    if (response.statusCode != 200) {
      throw Exception('checkpoint API returned ${response.statusCode}: ${response.body}');
    }
  }
}
