import 'dart:convert';
import 'package:http/http.dart' as http;

/// Central API Service for connecting Flutter frontend with FastAPI backend
class ApiService {
  // Base URL for the FastAPI backend (can be adjusted for emulator 10.0.2.2 or physical device IP)
  static const String baseUrl = 'http://localhost:8000/api';

  // Singleton pattern for application-wide service reuse
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal();

  static const Duration _timeoutDuration = Duration(seconds: 12);
  static const Map<String, String> _headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json',
  };

  /// Register a new farmer / user
  ///
  /// Sends [name], [email], [mobile], and [password] to POST /api/auth/register
  /// Returns a Map containing:
  /// - 'success': bool
  /// - 'message': String
  /// - 'data': dynamic (optional response body)
  Future<Map<String, dynamic>> registerUser({
    required String name,
    required String email,
    required String mobile,
    required String password,
  }) async {
    final uri = Uri.parse('$baseUrl/auth/register');

    final payload = {
      'name': name.trim(),
      'email': email.trim(),
      'mobile': mobile.trim(),
      'password': password,
    };

    try {
      final response = await http
          .post(
            uri,
            headers: _headers,
            body: jsonEncode(payload),
          )
          .timeout(_timeoutDuration);

      final Map<String, dynamic> responseData = _decodeResponse(response.body);

      if (response.statusCode == 200 || response.statusCode == 201) {
        return {
          'success': true,
          'message': responseData['message']?.toString() ??
              'Registration successful',
          'data': responseData,
        };
      } else {
        final errorMessage = responseData['detail']?.toString() ??
            responseData['message']?.toString() ??
            'Registration failed (${response.statusCode})';
        return {
          'success': false,
          'message': errorMessage,
          'statusCode': response.statusCode,
        };
      }
    } catch (e) {
      return {
        'success': false,
        'message':
            'Unable to connect to server. Please verify backend is running.',
        'error': e.toString(),
      };
    }
  }

  /// Authenticate and login an existing farmer / user
  ///
  /// Sends [email] and [password] to POST /api/auth/login
  /// Returns a Map containing:
  /// - 'success': bool
  /// - 'message': String
  /// - 'user_name': String? (name of the logged in farmer)
  /// - 'data': dynamic (optional response body)
  Future<Map<String, dynamic>> loginUser({
    required String email,
    required String password,
  }) async {
    final uri = Uri.parse('$baseUrl/auth/login');

    final payload = {
      'email': email.trim(),
      'password': password,
    };

    try {
      final response = await http
          .post(
            uri,
            headers: _headers,
            body: jsonEncode(payload),
          )
          .timeout(_timeoutDuration);

      final Map<String, dynamic> responseData = _decodeResponse(response.body);

      if (response.statusCode == 200) {
        final userName = responseData['user_name']?.toString() ?? 'Farmer';
        return {
          'success': true,
          'message': responseData['message']?.toString() ?? 'Login successful',
          'user_name': userName,
          'data': responseData,
        };
      } else {
        final errorMessage = responseData['detail']?.toString() ??
            responseData['message']?.toString() ??
            'Invalid email or password.';
        return {
          'success': false,
          'message': errorMessage,
          'statusCode': response.statusCode,
        };
      }
    } catch (e) {
      return {
        'success': false,
        'message':
            'Unable to connect to server. Please verify backend is running.',
        'error': e.toString(),
      };
    }
  }

  /// System health check
  Future<Map<String, dynamic>> getHealth() async {
    final uri = Uri.parse('$baseUrl/health');
    try {
      final response = await http.get(uri).timeout(const Duration(seconds: 5));
      return _decodeResponse(response.body);
    } catch (e) {
      return {'message': 'Backend unavailable', 'error': e.toString()};
    }
  }

  /// Helper to safely decode JSON body
  Map<String, dynamic> _decodeResponse(String body) {
    if (body.isEmpty) return {};
    try {
      final decoded = jsonDecode(body);
      if (decoded is Map<String, dynamic>) {
        return decoded;
      } else if (decoded is Map) {
        return Map<String, dynamic>.from(decoded);
      }
      return {'result': decoded};
    } catch (_) {
      return {'raw': body};
    }
  }
}
