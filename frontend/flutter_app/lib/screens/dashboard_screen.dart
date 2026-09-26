import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'crop_screen.dart';
import 'disease_screen.dart';
import 'fertilizer_screen.dart';
import 'login_screen.dart';
import 'market_screen.dart';
import 'weather_screen.dart';

class DashboardScreen extends StatefulWidget {
  final String? farmerName;

  const DashboardScreen({super.key, this.farmerName});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen>
    with SingleTickerProviderStateMixin {
  late String _displayName;
  late AnimationController _animController;
  late Animation<double> _fadeAnim;

  static const _primaryGreen = Color(0xFF1B5E20);
  static const _accentGreen = Color(0xFF4CAF50);
  static const _darkBg = Color(0xFF0D1F0D);

  final List<_ServiceCard> _services = const [
    _ServiceCard(
      title: 'Weather Advisory',
      subtitle: 'Rain alerts, temperature\n& farming forecast',
      icon: Icons.wb_sunny_rounded,
      gradientColors: [Color(0xFF1565C0), Color(0xFF42A5F5)],
      tag: 'Live',
    ),
    _ServiceCard(
      title: 'Fertilizer Guide',
      subtitle: 'Optimal NPK ratio\n& soil nutrients advice',
      icon: Icons.science_rounded,
      gradientColors: [Color(0xFFE65100), Color(0xFFFFA726)],
      tag: 'Smart',
    ),
    _ServiceCard(
      title: 'Crop Recommender',
      subtitle: 'Best matching crops\nfor soil & season',
      icon: Icons.eco_rounded,
      gradientColors: [Color(0xFF1B5E20), Color(0xFF66BB6A)],
      tag: 'AI',
    ),
    _ServiceCard(
      title: 'Market Prices',
      subtitle: 'Live mandi rates &\ncommodity trends',
      icon: Icons.trending_up_rounded,
      gradientColors: [Color(0xFF4A148C), Color(0xFFAB47BC)],
      tag: 'Live',
    ),
  ];

  @override
  void initState() {
    super.initState();
    _displayName =
        widget.farmerName ?? UserSession.userName ?? 'Farmer';
    _animController = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 600),
    );
    _fadeAnim =
        CurvedAnimation(parent: _animController, curve: Curves.easeOut);
    _animController.forward();
  }

  @override
  void dispose() {
    _animController.dispose();
    super.dispose();
  }

  void _handleLogout() {
    showDialog(
      context: context,
      builder: (ctx) => Dialog(
        backgroundColor: const Color(0xFF162B16),
        shape:
            RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Container(
                padding: const EdgeInsets.all(14),
                decoration: BoxDecoration(
                  color: Colors.red.withOpacity(0.15),
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.logout_rounded,
                    color: Color(0xFFFF5252), size: 32),
              ),
              const SizedBox(height: 16),
              Text('Sign Out?',
                  style: GoogleFonts.inter(
                      color: Colors.white,
                      fontSize: 20,
                      fontWeight: FontWeight.w700)),
              const SizedBox(height: 8),
              Text(
                'Are you sure you want to sign out of Smart Crop Advisory?',
                textAlign: TextAlign.center,
                style: GoogleFonts.inter(
                    color: Colors.white60, fontSize: 14, height: 1.4),
              ),
              const SizedBox(height: 24),
              Row(children: [
                Expanded(
                  child: OutlinedButton(
                    onPressed: () => Navigator.of(ctx).pop(),
                    style: OutlinedButton.styleFrom(
                      foregroundColor: Colors.white60,
                      side:
                          BorderSide(color: Colors.white.withOpacity(0.2)),
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                    child: Text('Cancel',
                        style: GoogleFonts.inter(fontWeight: FontWeight.w600)),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: ElevatedButton(
                    onPressed: () {
                      Navigator.of(ctx).pop();
                      UserSession.clearSession();
                      Navigator.pushAndRemoveUntil(
                        context,
                        MaterialPageRoute(
                            builder: (_) => const LoginScreen()),
                        (route) => false,
                      );
                    },
                    style: ElevatedButton.styleFrom(
                      backgroundColor: const Color(0xFFB71C1C),
                      foregroundColor: Colors.white,
                      shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(12)),
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                    child: Text('Sign Out',
                        style: GoogleFonts.inter(fontWeight: FontWeight.w600)),
                  ),
                ),
              ]),
            ],
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Container(
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [_darkBg, Color(0xFF111F11), Color(0xFF0A1A0A)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: SafeArea(
          child: FadeTransition(
            opacity: _fadeAnim,
            child: Column(
              children: [
                // Top Bar
                _buildTopBar(),

                // Scrollable Content
                Expanded(
                  child: SingleChildScrollView(
                    padding: const EdgeInsets.all(20),
                    child: Center(
                      child: ConstrainedBox(
                        constraints: const BoxConstraints(maxWidth: 1100),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            // Welcome Banner
                            _buildWelcomeBanner(),
                            const SizedBox(height: 28),

                            // Featured AI Disease Card
                            _buildFeaturedCard(context),
                            const SizedBox(height: 28),

                            // Section Label
                            Text(
                              'Advisory Services',
                              style: GoogleFonts.inter(
                                color: Colors.white,
                                fontSize: 18,
                                fontWeight: FontWeight.w700,
                                letterSpacing: -0.3,
                              ),
                            ),
                            const SizedBox(height: 4),
                            Text(
                              'Tap any service for instant AI-powered advice',
                              style: GoogleFonts.inter(
                                  color: Colors.white38, fontSize: 13),
                            ),
                            const SizedBox(height: 16),

                            // Services Grid
                            LayoutBuilder(builder: (context, constraints) {
                              final cols = constraints.maxWidth >= 800
                                  ? 4
                                  : constraints.maxWidth >= 500
                                      ? 2
                                      : 2;
                              return GridView.builder(
                                shrinkWrap: true,
                                physics: const NeverScrollableScrollPhysics(),
                                gridDelegate:
                                    SliverGridDelegateWithFixedCrossAxisCount(
                                  crossAxisCount: cols,
                                  crossAxisSpacing: 14,
                                  mainAxisSpacing: 14,
                                  childAspectRatio: constraints.maxWidth >= 800
                                      ? 1.0
                                      : 1.1,
                                ),
                                itemCount: _services.length,
                                itemBuilder: (context, i) =>
                                    _buildServiceCard(context, _services[i]),
                              );
                            }),
                            const SizedBox(height: 28),

                            // Stats Row
                            _buildStatsRow(),
                            const SizedBox(height: 20),
                          ],
                        ),
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildTopBar() {
    return Container(
      padding: const EdgeInsets.fromLTRB(20, 12, 16, 12),
      decoration: BoxDecoration(
        color: Colors.white.withOpacity(0.04),
        border: Border(
            bottom: BorderSide(color: Colors.white.withOpacity(0.08))),
      ),
      child: Row(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF2E7D32), Color(0xFF66BB6A)],
              ),
              borderRadius: BorderRadius.circular(10),
            ),
            child: const Icon(Icons.agriculture_rounded,
                color: Colors.white, size: 22),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              'Smart Crop Advisory',
              style: GoogleFonts.inter(
                color: Colors.white,
                fontWeight: FontWeight.w700,
                fontSize: 17,
              ),
            ),
          ),
          Container(
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.08),
              borderRadius: BorderRadius.circular(10),
            ),
            child: IconButton(
              icon: const Icon(Icons.logout_rounded,
                  color: Colors.white60, size: 20),
              tooltip: 'Sign Out',
              onPressed: _handleLogout,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildWelcomeBanner() {
    final hour = DateTime.now().hour;
    final greeting = hour < 12
        ? 'Good Morning'
        : hour < 17
            ? 'Good Afternoon'
            : 'Good Evening';

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        gradient: LinearGradient(
          colors: [
            _primaryGreen.withOpacity(0.5),
            _accentGreen.withOpacity(0.15),
          ],
          begin: Alignment.topLeft,
          end: Alignment.bottomRight,
        ),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: _accentGreen.withOpacity(0.2)),
      ),
      child: Row(
        children: [
          Container(
            width: 52,
            height: 52,
            decoration: BoxDecoration(
              gradient: const LinearGradient(
                colors: [Color(0xFF2E7D32), Color(0xFF81C784)],
              ),
              shape: BoxShape.circle,
              boxShadow: [
                BoxShadow(
                  color: _accentGreen.withOpacity(0.3),
                  blurRadius: 12,
                )
              ],
            ),
            child: Center(
              child: Text(
                _displayName.isNotEmpty
                    ? _displayName[0].toUpperCase()
                    : 'F',
                style: GoogleFonts.inter(
                    color: Colors.white,
                    fontSize: 22,
                    fontWeight: FontWeight.w800),
              ),
            ),
          ),
          const SizedBox(width: 16),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text('$greeting! 🌿',
                    style: GoogleFonts.inter(
                        color: Colors.white60, fontSize: 13)),
                const SizedBox(height: 2),
                Text(
                  _displayName,
                  style: GoogleFonts.inter(
                    color: Colors.white,
                    fontSize: 20,
                    fontWeight: FontWeight.w800,
                    letterSpacing: -0.3,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  'AI-powered farming intelligence at your fingertips',
                  style: GoogleFonts.inter(
                      color: Colors.white38, fontSize: 12),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
            decoration: BoxDecoration(
              color: _accentGreen.withOpacity(0.2),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: _accentGreen.withOpacity(0.4)),
            ),
            child: Row(children: [
              Container(
                width: 7,
                height: 7,
                decoration: const BoxDecoration(
                    color: _accentGreen, shape: BoxShape.circle),
              ),
              const SizedBox(width: 5),
              Text('Active',
                  style: GoogleFonts.inter(
                      color: _accentGreen,
                      fontSize: 11,
                      fontWeight: FontWeight.w600)),
            ]),
          ),
        ],
      ),
    );
  }

  Widget _buildFeaturedCard(BuildContext context) {
    return GestureDetector(
      onTap: () => Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => const DiseaseScreen()),
      ),
      child: Container(
        padding: const EdgeInsets.all(22),
        decoration: BoxDecoration(
          gradient: const LinearGradient(
            colors: [Color(0xFF1B5E20), Color(0xFF2E7D32), Color(0xFF43A047)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
          borderRadius: BorderRadius.circular(22),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF2E7D32).withOpacity(0.45),
              blurRadius: 24,
              offset: const Offset(0, 10),
            ),
          ],
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.15),
                borderRadius: BorderRadius.circular(18),
              ),
              child: const Icon(Icons.center_focus_strong_rounded,
                  size: 44, color: Colors.white),
            ),
            const SizedBox(width: 18),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(children: [
                    Flexible(
                      child: Text('Plant Disease Detection',
                          style: GoogleFonts.inter(
                            color: Colors.white,
                            fontSize: 18,
                            fontWeight: FontWeight.w800,
                            letterSpacing: -0.3,
                          )),
                    ),
                    const SizedBox(width: 8),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFD54F),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: Text('AI',
                          style: GoogleFonts.inter(
                              color: const Color(0xFF3E2723),
                              fontSize: 11,
                              fontWeight: FontWeight.w800)),
                    ),
                  ]),
                  const SizedBox(height: 6),
                  Text(
                    'Snap a crop leaf photo to instantly detect diseases and get AI treatment recommendations',
                    style: GoogleFonts.inter(
                        color: Colors.white.withOpacity(0.85),
                        fontSize: 13,
                        height: 1.4),
                  ),
                  const SizedBox(height: 10),
                  Row(children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white.withOpacity(0.18),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text('Scan Now →',
                          style: GoogleFonts.inter(
                              color: Colors.white,
                              fontSize: 12,
                              fontWeight: FontWeight.w600)),
                    ),
                  ]),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildServiceCard(BuildContext context, _ServiceCard service) {
    Widget destination;
    switch (service.title) {
      case 'Weather Advisory':
        destination = const WeatherScreen();
        break;
      case 'Fertilizer Guide':
        destination = const FertilizerScreen();
        break;
      case 'Crop Recommender':
        destination = const CropScreen();
        break;
      case 'Market Prices':
        destination = const MarketScreen();
        break;
      default:
        destination = const WeatherScreen();
    }

    return GestureDetector(
      onTap: () => Navigator.push(
        context,
        MaterialPageRoute(builder: (_) => destination),
      ),
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white.withOpacity(0.05),
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: Colors.white.withOpacity(0.1)),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Gradient Top Strip + Icon
            Container(
              height: 80,
              decoration: BoxDecoration(
                gradient: LinearGradient(
                  colors: service.gradientColors,
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                ),
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(18),
                  topRight: Radius.circular(18),
                ),
              ),
              child: Stack(children: [
                Center(
                  child: Icon(service.icon, size: 38, color: Colors.white),
                ),
                Positioned(
                  top: 8,
                  right: 10,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                        horizontal: 7, vertical: 2),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.2),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Text(service.tag,
                        style: GoogleFonts.inter(
                            color: Colors.white,
                            fontSize: 10,
                            fontWeight: FontWeight.w700)),
                  ),
                ),
              ]),
            ),

            // Text Content
            Expanded(
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      service.title,
                      style: GoogleFonts.inter(
                        color: Colors.white,
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                        letterSpacing: -0.2,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 4),
                    Text(
                      service.subtitle,
                      style: GoogleFonts.inter(
                          color: Colors.white38,
                          fontSize: 11,
                          height: 1.35),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 6),
                    Row(children: [
                      Text('Open →',
                          style: GoogleFonts.inter(
                              color: Colors.white30,
                              fontSize: 11,
                              fontWeight: FontWeight.w600)),
                    ]),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStatsRow() {
    return Row(
      children: [
        _buildStatChip(Icons.wb_sunny_rounded, 'Season', 'Kharif 2024',
            const Color(0xFFF57C00)),
        const SizedBox(width: 10),
        _buildStatChip(Icons.location_on_rounded, 'Region', 'India',
            const Color(0xFF1976D2)),
        const SizedBox(width: 10),
        _buildStatChip(Icons.verified_rounded, 'Status', 'Verified',
            _accentGreen),
      ],
    );
  }

  Widget _buildStatChip(
      IconData icon, String label, String value, Color color) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 12, horizontal: 12),
        decoration: BoxDecoration(
          color: color.withOpacity(0.08),
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: color.withOpacity(0.2)),
        ),
        child: Row(children: [
          Icon(icon, color: color, size: 16),
          const SizedBox(width: 8),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(label,
                    style: GoogleFonts.inter(
                        color: Colors.white38, fontSize: 10)),
                Text(value,
                    style: GoogleFonts.inter(
                        color: Colors.white,
                        fontWeight: FontWeight.w600,
                        fontSize: 12),
                    overflow: TextOverflow.ellipsis),
              ],
            ),
          ),
        ]),
      ),
    );
  }
}

/// Data class for service cards
class _ServiceCard {
  final String title;
  final String subtitle;
  final IconData icon;
  final List<Color> gradientColors;
  final String tag;

  const _ServiceCard({
    required this.title,
    required this.subtitle,
    required this.icon,
    required this.gradientColors,
    required this.tag,
  });
}
