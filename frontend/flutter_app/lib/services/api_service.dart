class ApiService {
  static const String baseUrl = 'http://localhost:8000/api';

  Future<Map<String, dynamic>> getHealth() async {
    return {'message': 'API endpoint placeholder'};
  }
}
