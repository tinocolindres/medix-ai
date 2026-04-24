import 'package:dio/dio.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';

class ApiService {
  static const String _baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://localhost:8000/api/v1',
  );

  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;

  late final Dio _dio;
  final _storage = const FlutterSecureStorage();

  ApiService._internal() {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 15),
      receiveTimeout: const Duration(seconds: 30),
      headers: {'Content-Type': 'application/json'},
    ));

    // Interceptor: inyecta JWT en cada request
    _dio.interceptors.add(InterceptorsWrapper(
      onRequest: (options, handler) async {
        final token = await _storage.read(key: 'jwt_token');
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        return handler.next(options);
      },
      onError: (error, handler) async {
        if (error.response?.statusCode == 401) {
          await _storage.delete(key: 'jwt_token');
          // Navegar a login (manejado por Riverpod auth state)
        }
        return handler.next(error);
      },
    ));
  }

  // ─────────────────────────────────────────────────────────────
  // AUTH
  // ─────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> login(String email, String password) async {
    final response = await _dio.post('/auth/login', data: {
      'email': email,
      'password': password,
    });
    final token = response.data['access_token'];
    await _storage.write(key: 'jwt_token', value: token);
    return response.data;
  }

  Future<Map<String, dynamic>> register(Map<String, dynamic> userData) async {
    final response = await _dio.post('/auth/register', data: userData);
    final token = response.data['access_token'];
    await _storage.write(key: 'jwt_token', value: token);
    return response.data;
  }

  Future<Map<String, dynamic>> getMe() async {
    final response = await _dio.get('/auth/me');
    return response.data;
  }

  Future<void> logout() async {
    await _storage.delete(key: 'jwt_token');
  }

  Future<bool> isLoggedIn() async {
    final token = await _storage.read(key: 'jwt_token');
    return token != null;
  }

  // ─────────────────────────────────────────────────────────────
  // CHAT IA
  // ─────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> sendChatMessage({
    required String message,
    String? sessionId,
    String? subjectId,
    String mode = 'chat',
  }) async {
    final response = await _dio.post('/analysis/chat', data: {
      'message': message,
      if (sessionId != null) 'session_id': sessionId,
      if (subjectId != null) 'subject_id': subjectId,
      'mode': mode,
    });
    return response.data;
  }

  // ─────────────────────────────────────────────────────────────
  // SOAP DICTATION
  // ─────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> generateSoapNote(String dictation, {String? patientContext}) async {
    final response = await _dio.post('/analysis/soap', data: {
      'dictation': dictation,
      if (patientContext != null) 'patient_context': patientContext,
    });
    return response.data;
  }

  // ─────────────────────────────────────────────────────────────
  // MEDSCAN VISION
  // ─────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> uploadScan({
    required List<int> imageBytes,
    required String fileName,
    required String mimeType,
    String scanType = 'other',
    String? patientContext,
  }) async {
    final formData = FormData.fromMap({
      'file': MultipartFile.fromBytes(
        imageBytes,
        filename: fileName,
        contentType: DioMediaType.parse(mimeType),
      ),
      'scan_type': scanType,
      if (patientContext != null) 'patient_context': patientContext,
    });

    final response = await _dio.post(
      '/upload/scan',
      data: formData,
      options: Options(contentType: 'multipart/form-data'),
    );
    return response.data;
  }

  // ─────────────────────────────────────────────────────────────
  // SESAL RAG
  // ─────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> querySESAL(String query) async {
    final response = await _dio.post('/analysis/sesal', data: {'query': query});
    return response.data;
  }

  // ─────────────────────────────────────────────────────────────
  // ECOE SIMULATOR
  // ─────────────────────────────────────────────────────────────

  Future<Map<String, dynamic>> startECOE(String caseId) async {
    final response = await _dio.post('/analysis/ecoe/start', data: {'case_id': caseId});
    return response.data;
  }
}

// Extension para métodos de Stripe (agregado en Sprint 2)
extension StripeApi on ApiService {
  Future<Map<String, dynamic>> createCheckout(String plan) async {
    final response = await _dio.post('/subscription/checkout', data: {'plan': plan});
    return response.data;
  }

  Future<Map<String, dynamic>> getSubscriptionStatus() async {
    final response = await _dio.get('/subscription/status');
    return response.data;
  }

  Future<String> getBillingPortalUrl() async {
    final response = await _dio.post('/subscription/portal');
    return response.data['portal_url'] as String;
  }
}

// Extension para Sprint 3 — Analytics, Feedback, FCM
extension Sprint3Api on ApiService {
  Future<void> submitFeedback({
    required int rating,
    String? module,
    String? message,
    String? appVersion,
  }) async {
    await _dio.post('/feedback', data: {
      'rating': rating,
      if (module != null) 'module': module,
      if (message != null) 'message': message,
      if (appVersion != null) 'app_version': appVersion,
    });
  }

  Future<void> registerFcmToken(String fcmToken) async {
    await _dio.post('/feedback/fcm-token', queryParameters: {'token': fcmToken});
  }
}
