import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/api_service.dart';
import 'dashboard_screen.dart';
import 'register_screen.dart';

/// In-memory session manager
class UserSession {
  static String? userEmail;
  static String? userName;
  static bool isLoggedIn = false;
  static bool rememberMe = true;

  static void setSession({
    required String email,
    required String name,
    required bool remember,
  }) {
    userEmail = email;
    userName = name;
    isLoggedIn = true;
    rememberMe = remember;
  }

  static void clearSession() {
    userEmail = null;
    userName = null;
    isLoggedIn = false;
    rememberMe = false;
  }
}

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen>
    with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _emailController;
  late final TextEditingController _passwordController;
  late AnimationController _animController;
  late Animation<double> _fadeAnim;
  late Animation<Offset> _slideAnim;

  bool _obscurePassword = true;
  bool _rememberMe = true;
  bool _isLoading = false;
  String? _errorMessage;

  static const _primaryGreen = Color(0xFF1B5E20);
  static const _accentGreen = Color(0xFF4CAF50);
  static const _darkBg = Color(0xFF0D1F0D);

  @override
  void initState() {
    super.initState();
    _emailController = TextEditingController(
      text: UserSession.rememberMe ? (UserSession.userEmail ?? '') : '',
    );
    _passwordController = TextEditingController();
    _rememberMe = UserSession.rememberMe;

    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );
    _fadeAnim = CurvedAnimation(parent: _animController, curve: Curves.easeOut);
    _slideAnim = Tween<Offset>(
      begin: const Offset(0, 0.08),
      end: Offset.zero,
    ).animate(CurvedAnimation(parent: _animController, curve: Curves.easeOut));
    _animController.forward();
  }

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _animController.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    FocusScope.of(context).unfocus();
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final email = _emailController.text.trim();
    final password = _passwordController.text;

    final result = await ApiService().loginUser(email: email, password: password);

    if (!mounted) return;

    if (result['success'] == true) {
      final name = result['user_name']?.toString() ?? 'Farmer';
      UserSession.setSession(email: email, name: name, remember: _rememberMe);

      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(children: [
            const Icon(Icons.check_circle_rounded, color: Colors.white),
            const SizedBox(width: 10),
            Expanded(
              child: Text('Welcome back, $name! 🌱',
                  style: GoogleFonts.inter(fontWeight: FontWeight.w600)),
            ),
          ]),
          backgroundColor: _accentGreen,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      );

      Navigator.pushReplacement(
        context,
        PageRouteBuilder(
          pageBuilder: (_, a1, a2) => DashboardScreen(farmerName: name),
          transitionsBuilder: (_, a1, a2, child) =>
              FadeTransition(opacity: a1, child: child),
          transitionDuration: const Duration(milliseconds: 400),
        ),
      );
    } else {
      setState(() {
        _errorMessage = result['message']?.toString() ??
            'Invalid email or password. Please try again.';
        _isLoading = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [_darkBg, Color(0xFF1A3A1A), Color(0xFF0D2E0D)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: Center(
            child: SingleChildScrollView(
              padding: const EdgeInsets.all(24),
              child: FadeTransition(
                opacity: _fadeAnim,
                child: SlideTransition(
                  position: _slideAnim,
                  child: ConstrainedBox(
                    constraints: const BoxConstraints(maxWidth: 460),
                    child: Column(
                      children: [
                        // Logo Section
                        Container(
                          padding: const EdgeInsets.all(20),
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            gradient: const LinearGradient(
                              colors: [Color(0xFF2E7D32), Color(0xFF66BB6A)],
                              begin: Alignment.topLeft,
                              end: Alignment.bottomRight,
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: _accentGreen.withOpacity(0.4),
                                blurRadius: 24,
                                spreadRadius: 2,
                              )
                            ],
                          ),
                          child: const Icon(Icons.agriculture_rounded,
                              size: 52, color: Colors.white),
                        ),
                        const SizedBox(height: 20),
                        Text(
                          'Smart Crop Advisory',
                          style: GoogleFonts.inter(
                            fontSize: 26,
                            fontWeight: FontWeight.w800,
                            color: Colors.white,
                            letterSpacing: -0.5,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'AI-powered farming intelligence',
                          style: GoogleFonts.inter(
                            fontSize: 14,
                            color: Colors.white54,
                          ),
                        ),
                        const SizedBox(height: 36),

                        // Glass Card
                        Container(
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.05),
                            borderRadius: BorderRadius.circular(24),
                            border: Border.all(
                              color: Colors.white.withOpacity(0.12),
                            ),
                            boxShadow: [
                              BoxShadow(
                                color: Colors.black.withOpacity(0.3),
                                blurRadius: 32,
                                offset: const Offset(0, 16),
                              ),
                            ],
                          ),
                          child: Padding(
                            padding: const EdgeInsets.all(28),
                            child: Form(
                              key: _formKey,
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.stretch,
                                children: [
                                  Text(
                                    'Welcome Back 👋',
                                    style: GoogleFonts.inter(
                                      fontSize: 22,
                                      fontWeight: FontWeight.w700,
                                      color: Colors.white,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    'Sign in to your account',
                                    style: GoogleFonts.inter(
                                      fontSize: 14,
                                      color: Colors.white54,
                                    ),
                                  ),
                                  const SizedBox(height: 24),

                                  // Error Banner
                                  if (_errorMessage != null) ...[
                                    Container(
                                      padding: const EdgeInsets.all(12),
                                      decoration: BoxDecoration(
                                        color: Colors.red.withOpacity(0.12),
                                        borderRadius: BorderRadius.circular(12),
                                        border: Border.all(
                                            color: Colors.red.withOpacity(0.3)),
                                      ),
                                      child: Row(children: [
                                        const Icon(Icons.error_outline_rounded,
                                            color: Color(0xFFFF5252), size: 20),
                                        const SizedBox(width: 10),
                                        Expanded(
                                          child: Text(_errorMessage!,
                                              style: GoogleFonts.inter(
                                                color: const Color(0xFFFF8A80),
                                                fontSize: 13,
                                              )),
                                        ),
                                      ]),
                                    ),
                                    const SizedBox(height: 18),
                                  ],

                                  // Email
                                  _buildField(
                                    controller: _emailController,
                                    label: 'Email Address',
                                    hint: 'farmer@example.com',
                                    icon: Icons.email_outlined,
                                    keyboardType: TextInputType.emailAddress,
                                    validator: (v) {
                                      if (v == null || v.trim().isEmpty)
                                        return 'Email is required';
                                      if (!RegExp(
                                              r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')
                                          .hasMatch(v.trim()))
                                        return 'Enter a valid email address';
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 16),

                                  // Password
                                  _buildField(
                                    controller: _passwordController,
                                    label: 'Password',
                                    hint: '••••••••',
                                    icon: Icons.lock_outline_rounded,
                                    obscureText: _obscurePassword,
                                    onFieldSubmitted: (_) => _handleLogin(),
                                    suffixIcon: IconButton(
                                      icon: Icon(
                                        _obscurePassword
                                            ? Icons.visibility_off_outlined
                                            : Icons.visibility_outlined,
                                        color: Colors.white38,
                                        size: 20,
                                      ),
                                      onPressed: () => setState(() =>
                                          _obscurePassword = !_obscurePassword),
                                    ),
                                    validator: (v) {
                                      if (v == null || v.isEmpty)
                                        return 'Password is required';
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 14),

                                  // Remember Me
                                  GestureDetector(
                                    onTap: () => setState(
                                        () => _rememberMe = !_rememberMe),
                                    child: Row(children: [
                                      SizedBox(
                                        height: 22,
                                        width: 22,
                                        child: Checkbox(
                                          value: _rememberMe,
                                          activeColor: _accentGreen,
                                          checkColor: Colors.white,
                                          side: const BorderSide(
                                              color: Colors.white38),
                                          shape: RoundedRectangleBorder(
                                              borderRadius:
                                                  BorderRadius.circular(4)),
                                          onChanged: (v) => setState(
                                              () => _rememberMe = v ?? false),
                                        ),
                                      ),
                                      const SizedBox(width: 10),
                                      Text('Remember me',
                                          style: GoogleFonts.inter(
                                              color: Colors.white60,
                                              fontSize: 13)),
                                    ]),
                                  ),
                                  const SizedBox(height: 24),

                                  // Login Button
                                  _buildPrimaryButton(
                                    label: 'Sign In',
                                    isLoading: _isLoading,
                                    onPressed: _handleLogin,
                                  ),
                                  const SizedBox(height: 16),

                                  // Divider
                                  Row(children: [
                                    Expanded(
                                        child: Divider(
                                            color: Colors.white.withOpacity(0.1))),
                                    Padding(
                                      padding: const EdgeInsets.symmetric(
                                          horizontal: 12),
                                      child: Text('or',
                                          style: GoogleFonts.inter(
                                              color: Colors.white38,
                                              fontSize: 13)),
                                    ),
                                    Expanded(
                                        child: Divider(
                                            color: Colors.white.withOpacity(0.1))),
                                  ]),
                                  const SizedBox(height: 16),

                                  // Create Account Button
                                  SizedBox(
                                    height: 50,
                                    child: OutlinedButton(
                                      onPressed: () => Navigator.pushReplacement(
                                        context,
                                        MaterialPageRoute(
                                            builder: (_) =>
                                                const RegisterScreen()),
                                      ),
                                      style: OutlinedButton.styleFrom(
                                        foregroundColor: _accentGreen,
                                        side: BorderSide(
                                            color: _accentGreen.withOpacity(0.5),
                                            width: 1.5),
                                        shape: RoundedRectangleBorder(
                                            borderRadius:
                                                BorderRadius.circular(14)),
                                      ),
                                      child: Text('Create Account',
                                          style: GoogleFonts.inter(
                                              fontWeight: FontWeight.w600,
                                              fontSize: 15)),
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 24),
                        Text(
                          '© 2024 Smart Crop Advisory System',
                          style: GoogleFonts.inter(
                              color: Colors.white24, fontSize: 12),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildField({
    required TextEditingController controller,
    required String label,
    required String hint,
    required IconData icon,
    TextInputType? keyboardType,
    bool obscureText = false,
    Widget? suffixIcon,
    String? Function(String?)? validator,
    void Function(String)? onFieldSubmitted,
  }) {
    return TextFormField(
      controller: controller,
      obscureText: obscureText,
      keyboardType: keyboardType,
      onFieldSubmitted: onFieldSubmitted,
      style: GoogleFonts.inter(color: Colors.white, fontSize: 15),
      validator: validator,
      decoration: InputDecoration(
        labelText: label,
        hintText: hint,
        labelStyle: GoogleFonts.inter(color: Colors.white54, fontSize: 14),
        hintStyle: GoogleFonts.inter(color: Colors.white24, fontSize: 14),
        prefixIcon: Icon(icon, color: _accentGreen, size: 20),
        suffixIcon: suffixIcon,
        filled: true,
        fillColor: Colors.white.withOpacity(0.06),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: Colors.white.withOpacity(0.15)),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: BorderSide(color: Colors.white.withOpacity(0.15)),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: _accentGreen, width: 1.5),
        ),
        errorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: Color(0xFFFF5252), width: 1.5),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide: const BorderSide(color: Color(0xFFFF5252), width: 1.5),
        ),
        errorStyle: GoogleFonts.inter(color: const Color(0xFFFF8A80), fontSize: 12),
      ),
    );
  }

  Widget _buildPrimaryButton({
    required String label,
    required bool isLoading,
    required VoidCallback onPressed,
  }) {
    return SizedBox(
      height: 52,
      child: DecoratedBox(
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF2E7D32), Color(0xFF66BB6A)],
            begin: Alignment.centerLeft,
            end: Alignment.centerRight,
          ),
          borderRadius: BorderRadius.circular(14),
          boxShadow: [
            BoxShadow(
              color: _accentGreen.withOpacity(0.35),
              blurRadius: 16,
              offset: const Offset(0, 6),
            ),
          ],
        ),
        child: ElevatedButton(
          onPressed: isLoading ? null : onPressed,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.transparent,
            shadowColor: Colors.transparent,
            shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(14)),
          ),
          child: isLoading
              ? const SizedBox(
                  height: 22,
                  width: 22,
                  child: CircularProgressIndicator(
                      strokeWidth: 2.5, color: Colors.white),
                )
              : Text(label,
                  style: GoogleFonts.inter(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: Colors.white)),
        ),
      ),
    );
  }
}
