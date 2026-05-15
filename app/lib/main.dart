import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'screens/home_screen.dart';
import 'screens/disease_detection_screen.dart';
import 'screens/report_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/login_screen.dart';
import 'services/auth_service.dart';
import 'services/navigation_service.dart';
import 'services/translation_service.dart';
import 'services/location_service.dart';

void main() {
  runApp(const KisanSetuApp());
}

class KisanSetuApp extends StatelessWidget {
  const KisanSetuApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ListenableBuilder(
      listenable: TranslationService(),
      builder: (context, _) {
        return MaterialApp(
          title: 'KisanSetu',
          debugShowCheckedModeBanner: false,
          theme: ThemeData(
            fontFamily: 'Inter',
            colorScheme: ColorScheme.fromSeed(
              seedColor: const Color(0xFF2E7D32),
              primary: const Color(0xFF4CAF50),
              secondary: const Color(0xFF81C784),
              surface: Colors.white,
            ),
            useMaterial3: true,
          ),
          home: ListenableBuilder(
            listenable: AuthService(),
            builder: (context, _) {
              if (AuthService().isLoggedIn) {
                return const RootNavigator();
              } else {
                return const LoginScreen();
              }
            },
          ),
        );
      },
    );
  }
}

class RootNavigator extends StatefulWidget {
  const RootNavigator({super.key});

  @override
  State<RootNavigator> createState() => _RootNavigatorState();
}

class _RootNavigatorState extends State<RootNavigator> {
  DateTime? lastPressed;

  @override
  void initState() {
    super.initState();
    _handleLocation();
  }

  Future<void> _handleLocation() async {
    final pos = await LocationService().getCurrentPosition();
    if (pos != null) {
      final name = await LocationService().getAddressFromLatLng(pos.latitude, pos.longitude);
      if (name != null) {
        AuthService().updateLocation(name, lat: pos.latitude, lng: pos.longitude);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final navService = NavigationService();

    final List<Widget> _screens = [
      const HomeScreen(),
      const DiseaseDetectionScreen(),
      const ReportScreen(),
      const ProfileScreen(),
    ];

    return ListenableBuilder(
      listenable: navService,
      builder: (context, _) {
        return PopScope(
          canPop: false,
          onPopInvoked: (didPop) async {
            if (didPop) return;
            
            if (navService.currentIndex != 0) {
              navService.changeIndex(0);
            } else {
              final now = DateTime.now();
              if (lastPressed == null || now.difference(lastPressed!) > const Duration(seconds: 2)) {
                lastPressed = now;
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(
                    content: Text('press_again_exit'.tr.isEmpty ? 'Press again to exit' : 'press_again_exit'.tr),
                    duration: const Duration(seconds: 2),
                    backgroundColor: Colors.green[800],
                    behavior: SnackBarBehavior.floating,
                  ),
                );
              } else {
                SystemNavigator.pop();
              }
            }
          },
          child: Scaffold(
            body: IndexedStack(
              index: navService.currentIndex,
              children: _screens,
            ),
            bottomNavigationBar: NavigationBar(
              selectedIndex: navService.currentIndex,
              onDestinationSelected: (index) {
                navService.changeIndex(index);
              },
              backgroundColor: Colors.white,
              indicatorColor: const Color(0xFFE8F5E9),
              destinations: [
                NavigationDestination(
                  icon: const Icon(Icons.home_outlined),
                  selectedIcon: const Icon(Icons.home, color: Color(0xFF2E7D32)),
                  label: 'home'.tr,
                ),
                NavigationDestination(
                  icon: const Icon(Icons.document_scanner_outlined),
                  selectedIcon: const Icon(Icons.document_scanner, color: Color(0xFF2E7D32)),
                  label: 'scan'.tr,
                ),
                NavigationDestination(
                  icon: const Icon(Icons.analytics_outlined),
                  selectedIcon: const Icon(Icons.analytics, color: Color(0xFF2E7D32)),
                  label: 'reports'.tr,
                ),
                NavigationDestination(
                  icon: const Icon(Icons.person_outline),
                  selectedIcon: const Icon(Icons.person, color: Color(0xFF2E7D32)),
                  label: 'profile'.tr,
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
