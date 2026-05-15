import 'package:flutter/material.dart';
import '../services/auth_service.dart';
import '../services/translation_service.dart';
import '../services/location_service.dart';

class ProfileScreen extends StatelessWidget {
  const ProfileScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final authService = AuthService();
    final transService = TranslationService();

    return Scaffold(
      backgroundColor: const Color(0xFFF7FBF7),
      appBar: AppBar(
        title: Text('profile'.tr, style: const TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.transparent,
        elevation: 0,
        foregroundColor: Colors.green[900],
        centerTitle: true,
      ),
      body: ListenableBuilder(
        listenable: authService,
        builder: (context, _) {
          return ListView(
            padding: const EdgeInsets.all(24),
            children: [
              Center(
                child: CircleAvatar(
                  radius: 50,
                  backgroundColor: Colors.green[100],
                  child: Icon(Icons.person, size: 60, color: Colors.green[800]),
                ),
              ),
              const SizedBox(height: 16),
              Center(
                child: Text(
                  authService.userName,
                  style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold),
                ),
              ),
              Center(
                child: Text(
                  authService.phoneNumber,
                  style: const TextStyle(fontSize: 16, color: Colors.grey),
                ),
              ),
              const SizedBox(height: 32),
              _buildSettingsTile(
                Icons.location_on_outlined, 
                'change_location'.tr, 
                authService.locationName,
                onTap: () async {
                  final pos = await LocationService().getCurrentPosition();
                  if (pos != null) {
                    final name = await LocationService().getAddressFromLatLng(pos.latitude, pos.longitude);
                    if (name != null) {
                      AuthService().updateLocation(name, lat: pos.latitude, lng: pos.longitude);
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(content: Text('Location updated to $name')),
                      );
                    }
                  }
                },
              ),
              
              // Language Dropdown
              Container(
                margin: const EdgeInsets.only(bottom: 12),
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                ),
                child: Row(
                  children: [
                    Icon(Icons.language_outlined, color: Colors.green[700]),
                    const SizedBox(width: 16),
                    Expanded(
                      child: Text(
                        'language'.tr,
                        style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 16),
                      ),
                    ),
                    ListenableBuilder(
                      listenable: transService,
                      builder: (context, _) {
                        return DropdownButton<Language>(
                          value: transService.currentLanguage,
                          underline: const SizedBox(),
                          icon: Icon(Icons.keyboard_arrow_down, color: Colors.grey[400]),
                          onChanged: (Language? newValue) {
                            if (newValue != null) {
                              transService.setLanguage(newValue);
                            }
                          },
                          items: [
                            DropdownMenuItem(value: Language.english, child: Text('English')),
                            DropdownMenuItem(value: Language.hindi, child: Text('हिंदी')),
                            DropdownMenuItem(value: Language.marathi, child: Text('मराठी')),
                          ],
                        );
                      },
                    ),
                  ],
                ),
              ),
              
              _buildSettingsTile(Icons.notifications_outlined, 'Notifications', 'On'),
              const SizedBox(height: 32),
              TextButton.icon(
                onPressed: () => _showLogoutDialog(context),
                icon: const Icon(Icons.logout, color: Colors.red),
                label: Text('logout'.tr, style: const TextStyle(color: Colors.red, fontSize: 16)),
              ),
            ],
          );
        },
      ),
    );
  }

  void _showLogoutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        backgroundColor: const Color(0xFFF7FBF7),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
        title: Text('Logout', style: TextStyle(color: Colors.green[900], fontWeight: FontWeight.bold)),
        content: const Text('Are you sure you want to log out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel', style: TextStyle(color: Colors.grey[600])),
          ),
          ElevatedButton(
            onPressed: () {
              Navigator.pop(context);
              AuthService().logout();
            },
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.red[50],
              foregroundColor: Colors.red,
              elevation: 0,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
            ),
            child: const Text('Logout', style: TextStyle(fontWeight: FontWeight.bold)),
          ),
        ],
      ),
    );
  }

  Widget _buildSettingsTile(IconData icon, String title, String subtitle, {VoidCallback? onTap}) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
      ),
      child: ListTile(
        onTap: onTap,
        leading: Icon(icon, color: Colors.green[700]),
        title: Text(title, style: const TextStyle(fontWeight: FontWeight.w600)),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.chevron_right, color: Colors.grey),
      ),
    );
  }
}
