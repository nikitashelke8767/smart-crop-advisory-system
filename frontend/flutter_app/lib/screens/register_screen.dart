import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../services/api_service.dart';
import 'login_screen.dart';

class RegisterScreen extends StatefulWidget {
  const RegisterScreen({super.key});

  @override
  State<RegisterScreen> createState() => _RegisterScreenState();
}

class _RegisterScreenState extends State<RegisterScreen>
    with SingleTickerProviderStateMixin {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _mobileController = TextEditingController();
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();

  late AnimationController _animController;
  late Animation<double> _fadeAnim;
  late Animation<Offset> _slideAnim;

  bool _obscurePassword = true;
  bool _obscureConfirmPassword = true;
  bool _isLoading = false;
  String? _errorMessage;

  static const _primaryGreen = Color(0xFF1B5E20);
  static const _accentGreen = Color(0xFF4CAF50);
  static const _darkBg = Color(0xFF0D1F0D);

  @override
  void initState() {
    super.initState();
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
    _nameController.dispose();
    _emailController.dispose();
    _mobileController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    _animController.dispose();
    super.dispose();
  }

  Future<void> _handleRegister() async {
    FocusScope.of(context).unfocus();
    if (!_formKey.currentState!.validate()) return;

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final result = await ApiService().registerUser(
      name: _nameController.text,
      email: _emailController.text,
      mobile: _mobileController.text,
      password: _passwordController.text,
    );

    if (!mounted) return;

    if (result['success'] == true) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(children: [
            const Icon(Icons.check_circle_rounded, color: Colors.white),
            const SizedBox(width: 10),
            Expanded(
              child: Text('Account created! Please sign in. 🌱',
                  style: GoogleFonts.inter(fontWeight: FontWeight.w600)),
            ),
          ]),
          backgroundColor: _accentGreen,
          behavior: SnackBarBehavior.floating,
          shape:
              RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
        ),
      );

      Navigator.pushReplacement(
        context,
        PageRouteBuilder(
          pageBuilder: (_, a1, a2) => const LoginScreen(),
          transitionsBuilder: (_, a1, a2, child) =>
              FadeTransition(opacity: a1, child: child),
          transitionDuration: const Duration(milliseconds: 400),
        ),
      );
    } else {
      setState(() {
        _errorMessage = result['message']?.toString() ??
            'Registration failed. Please check your details.';
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
                    constraints: const BoxConstraints(maxWidth: 480),
                    child: Column(
                      children: [
                        // Logo
                        Container(
                          padding: const EdgeInsets.all(18),
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
                          child: const Icon(Icons.grass_rounded,
                              size: 44, color: Colors.white),
                        ),
                        const SizedBox(height: 18),
                        Text(
                          'Create Your Account',
                          style: GoogleFonts.inter(
                            fontSize: 24,
                            fontWeight: FontWeight.w800,
                            color: Colors.white,
                            letterSpacing: -0.5,
                          ),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          'Join thousands of smart farmers',
                          style: GoogleFonts.inter(
                              fontSize: 14, color: Colors.white54),
                        ),
                        const SizedBox(height: 30),

                        // Glass Card
                        Container(
                          decoration: BoxDecoration(
                            color: Colors.white.withOpacity(0.05),
                            borderRadius: BorderRadius.circular(24),
                            border: Border.all(
                                color: Colors.white.withOpacity(0.12)),
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
                                  // Progress Indicator
                                  _buildStepBadge(),
                                  const SizedBox(height: 24),

                                  // Error Banner
                                  if (_errorMessage != null) ...[
                                    Container(
                                      padding: const EdgeInsets.all(12),
                                      decoration: BoxDecoration(
                                        color: Colors.red.withOpacity(0.12),
                                        borderRadius:
                                            BorderRadius.circular(12),
                                        border: Border.all(
                                            color:
                                                Colors.red.withOpacity(0.3)),
                                      ),
                                      child: Row(children: [
                                        const Icon(
                                            Icons.error_outline_rounded,
                                            color: Color(0xFFFF5252),
                                            size: 20),
                                        const SizedBox(width: 10),
                                        Expanded(
                                          child: Text(_errorMessage!,
                                              style: GoogleFonts.inter(
                                                color:
                                                    const Color(0xFFFF8A80),
                                                fontSize: 13,
                                              )),
                                        ),
                                      ]),
                                    ),
                                    const SizedBox(height: 18),
                                  ],

                                  // Full Name
                                  _buildField(
                                    controller: _nameController,
                                    label: 'Full Name',
                                    hint: 'e.g. Ramesh Patel',
                                    icon: Icons.person_outline_rounded,
                                    validator: (v) {
                                      if (v == null || v.trim().isEmpty)
                                        return 'Full name is required';
                                      if (v.trim().length < 2)
                                        return 'Name must be at least 2 characters';
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 14),

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
                                  const SizedBox(height: 14),

                                  // Mobile
                                  _buildField(
                                    controller: _mobileController,
                                    label: 'Mobile Number',
                                    hint: '9876543210',
                                    icon: Icons.phone_android_rounded,
                                    keyboardType: TextInputType.phone,
                                    validator: (v) {
                                      if (v == null || v.trim().isEmpty)
                                        return 'Mobile number is required';
                                      final digits =
                                          v.replaceAll(RegExp(r'[\s\-]'), '');
                                      if (!RegExp(r'^[0-9]{10}$')
                                          .hasMatch(digits))
                                        return 'Enter a valid 10-digit mobile number';
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 14),

                                  // Password
                                  _buildField(
                                    controller: _passwordController,
                                    label: 'Password',
                                    hint: 'Minimum 6 characters',
                                    icon: Icons.lock_outline_rounded,
                                    obscureText: _obscurePassword,
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
                                      if (v.length < 6)
                                        return 'Password must be at least 6 characters';
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 14),

                                  // Confirm Password
                                  _buildField(
                                    controller: _confirmPasswordController,
                                    label: 'Confirm Password',
                                    hint: 'Re-enter your password',
                                    icon: Icons.lock_reset_outlined,
                                    obscureText: _obscureConfirmPassword,
                                    onFieldSubmitted: (_) => _handleRegister(),
                                    suffixIcon: IconButton(
                                      icon: Icon(
                                        _obscureConfirmPassword
                                            ? Icons.visibility_off_outlined
                                            : Icons.visibility_outlined,
                                        color: Colors.white38,
                                        size: 20,
                                      ),
                                      onPressed: () => setState(() =>
                                          _obscureConfirmPassword =
                                              !_obscureConfirmPassword),
                                    ),
                                    validator: (v) {
                                      if (v == null || v.isEmpty)
                                        return 'Please confirm your password';
                                      if (v != _passwordController.text)
                                        return 'Passwords do not match';
                                      return null;
                                    },
                                  ),
                                  const SizedBox(height: 26),

                                  // Register Button
                                  _buildPrimaryButton(
                                    label: 'Create Account',
                                    isLoading: _isLoading,
                                    onPressed: _handleRegister,
                                  ),
                                  const SizedBox(height: 20),

                                  // Already have account
                                  Row(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Text('Already have an account? ',
                                          style: GoogleFonts.inter(
                                              color: Colors.white38,
                                              fontSize: 14)),
                                      GestureDetector(
                                        onTap: () => Navigator.pushReplacement(
                                          context,
                                          MaterialPageRoute(
                                              builder: (_) =>
                                                  const LoginScreen()),
                                        ),
                                        child: Text('Sign In',
                                            style: GoogleFonts.inter(
                                              color: _accentGreen,
                                              fontWeight: FontWeight.w700,
                                              fontSize: 14,
                                            )),
                                      ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ),
                        const SizedBox(height: 24),
                        Text('© 2024 Smart Crop Advisory System',
                            style: GoogleFonts.inter(
                                color: Colors.white24, fontSize: 12)),
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

  Widget _buildStepBadge() {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 5),
          decoration: BoxDecoration(
            color: _accentGreen.withOpacity(0.15),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(color: _accentGreen.withOpacity(0.3)),
          ),
          child: Row(children: [
            const Icon(Icons.person_add_alt_1_rounded,
                color: _accentGreen, size: 16),
            const SizedBox(width: 6),
            Text('New Farmer Registration',
                style: GoogleFonts.inter(
                    color: _accentGreen,
                    fontSize: 12,
                    fontWeight: FontWeight.w600)),
          ]),
        ),
      ],
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
          borderSide:
              const BorderSide(color: Color(0xFFFF5252), width: 1.5),
        ),
        focusedErrorBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(14),
          borderSide:
              const BorderSide(color: Color(0xFFFF5252), width: 1.5),
        ),
        errorStyle: GoogleFonts.inter(
            color: const Color(0xFFFF8A80), fontSize: 12),
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
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
