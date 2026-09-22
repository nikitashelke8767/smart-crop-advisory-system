class AuthService {
  Future<bool> login(String username, String password) async {
    return username.isNotEmpty && password.isNotEmpty;
  }
}
