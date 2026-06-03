import 'dart:convert';
import 'package:http/http.dart' as http;
import '../models/deep_analysis.dart';

class DeepAnalysisService {
  final String baseUrl;

  DeepAnalysisService(this.baseUrl);

  Future<DeepReview> submitReview({
    required String title,
    required List<String> paragraphs,
    required String author,
    required String tag,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/review'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'title': title,
        'paragraphs': paragraphs,
        'author': author,
        'tag': tag,
      }),
    );

    if (response.statusCode == 200) {
      return DeepReview.fromJson(jsonDecode(response.body));
    }

    String detail = '';
    try {
      final body = jsonDecode(response.body);
      detail = body['detail']?.toString() ?? '';
    } catch (_) {}

    throw Exception('深度分析请求失败 ($response.statusCode)${detail.isNotEmpty ? ': $detail' : ''}');
  }
}
