// Written by Tim Hudson - Last Updated 4/1/2025
// Written with the assistance of Openstack, Google Codelabs and ChatGPT

// This code is responsible for the account page that is displayed once a user signs in with an account
// This code has two main functions: Allow the user to set a home address and Allow the user to set a favorite garage

// This page is accessed through the account tab once a user signs in or signs up

import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:google_places_flutter/google_places_flutter.dart';
import '../widgets/appbar_datetime_center.dart';

class AccountPage extends StatefulWidget {
  const AccountPage({super.key});

  @override
  State<AccountPage> createState() => _AccountPageState();
}

class _AccountPageState extends State<AccountPage> {
  String? username;
  String? homeAddress;
  bool isLoading = true;
  List<String> savedAddresses = [];

  final TextEditingController _addressController = TextEditingController();

  // API key for Google Places Autocomplete
  final String googleApiKey =
      'AIzaSyBFrTsiYcpETNVw4fnwXZHREUx8XvB91jQ'; // <-- Replace with your actual API Key

  @override
  void initState() {
    super.initState();
    _getUserData();
  }

  @override
  void dispose() {
    _addressController.dispose();
    super.dispose();
  }

  Future<void> _deleteSavedAddress(String address) async {
    final User? user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      final List<String> updatedAddresses = List<String>.from(savedAddresses)
        ..remove(address);

      await FirebaseFirestore.instance.collection('users').doc(user.uid).update({
        'savedAddresses': updatedAddresses,
      });

      setState(() {
        savedAddresses = updatedAddresses;
      });
    }
  }

  // Grabs the needed data from the database
  Future<void> _getUserData() async {
    final User? user = FirebaseAuth.instance.currentUser;

    if (user != null) {
      try {
        final DocumentSnapshot userDoc =
            await FirebaseFirestore.instance.collection('users').doc(user.uid).get();

        if (userDoc.exists) {
          final data = userDoc.data() as Map<String, dynamic>;
          List<String> loadedAddresses = [];
          if (data['savedAddresses'] != null && data['savedAddresses'] is List) {
            loadedAddresses = List<String>.from(data['savedAddresses']);
          }
          setState(() {
            username = data['username'];
            homeAddress = data['homeAddress'];
            _addressController.text = homeAddress ?? '';
            savedAddresses = loadedAddresses;
            isLoading = false;
          });
        } else {
          setState(() {
            isLoading = false;
          });
        }
      } catch (e) {
        setState(() {
          isLoading = false;
        });
        print('Error fetching user data: $e');
      }
    } else {
      setState(() {
        isLoading = false;
      });
    }
  }

  // Updates the home address once the save address button is completed
  Future<void> _updateHomeAddress() async {
    final User? user = FirebaseAuth.instance.currentUser;
    if (user != null) {
      final String address = _addressController.text.trim();

      if (address.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please enter a valid address.')),
        );
        return;
      }

      try {
        final List<String> updatedAddresses = List<String>.from(savedAddresses);
        if (!updatedAddresses.contains(address)) {
          updatedAddresses.add(address);
        }
        await FirebaseFirestore.instance.collection('users').doc(user.uid).update({
          'homeAddress': address,
          'savedAddresses': updatedAddresses,
        });

        setState(() {
          homeAddress = address;
          savedAddresses = updatedAddresses;
        });

        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Home address updated successfully!')),
        );
      } catch (e) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Error updating address: $e')),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final User? user = FirebaseAuth.instance.currentUser;
    final mediaQuery = MediaQuery.of(context);
    final double topPanelInset = mediaQuery.padding.top + kToolbarHeight + 12;
    final double bottomPanelInset = mediaQuery.padding.bottom + 12;
    const double panelVerticalOffset = 0;
    final double pageHorizontalPadding =
        (mediaQuery.size.width * 0.028).clamp(14.0, 34.0).toDouble();
    final double containerWidth =
        (mediaQuery.size.width * 0.80).clamp(320.0, 1100.0).toDouble();

    return Scaffold(
      backgroundColor: const Color.fromRGBO(0, 0, 0, 1),
      extendBody: true,
      extendBodyBehindAppBar: true,
      appBar: AppBar(
        title: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Text(
              'Account',
              style: GoogleFonts.montserrat(fontWeight: FontWeight.w500),
            ),
            const SizedBox(width: 8),
            IconButton(
              icon: const Icon(Icons.help_outline),
              tooltip: 'Instructions',
              onPressed: () {
                showDialog(
                  context: context,
                  builder: (context) => AlertDialog(
                    title: const Text('Instructions'),
                    content: const Text(
                      'This page allows you to manage your account settings, including updating your home address and viewing saved addresses.',
                    ),
                    actions: [
                      TextButton(
                        onPressed: () => Navigator.of(context).pop(),
                        child: const Text('Close'),
                      ),
                    ],
                  ),
                );
              },
            ),
          ],
        ),
        backgroundColor: Colors.transparent,
        foregroundColor: const Color.fromRGBO(255, 255, 255, 1),
        elevation: 0,
        scrolledUnderElevation: 0,
        shadowColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
        flexibleSpace: const AppBarDateTimeCenter(),
        actions: [
          IconButton(
            icon: const Icon(Icons.logout),
            tooltip: 'Sign Out',
            onPressed: () async {
              await FirebaseAuth.instance.signOut();
              if (context.mounted) {
                Navigator.pop(context);
              }
            },
          ),
        ],
      ),
      body: Container(
        width: double.infinity,
        height: double.infinity,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            begin: Alignment.bottomLeft,
            end: Alignment.topRight,
            colors: [
              Color.fromRGBO(0, 0, 0, 1),
              Color.fromRGBO(69, 0, 132, 1),
            ],
          ),
        ),
        child: Stack(
          children: [
            Positioned.fill(
              child: Padding(
                padding: EdgeInsets.only(
                  top: topPanelInset,
                  left: pageHorizontalPadding,
                  right: pageHorizontalPadding,
                  bottom: bottomPanelInset,
                ),
                child: Transform.translate(
                  offset: const Offset(0, panelVerticalOffset),
                  child: isLoading
                      ? const Center(child: CircularProgressIndicator())
                      : user != null
                          ? Center(
                              child: SizedBox(
                                width: containerWidth,
                                height: double.infinity,
                                child: LayoutBuilder(
                                  builder: (context, constraints) {
                                    final bool isWide = constraints.maxWidth >= 960;

                                    final Widget profileCard = Container(
                                      width: double.infinity,
                                      padding: const EdgeInsets.all(18),
                                      decoration: BoxDecoration(
                                        color: const Color.fromRGBO(247, 247, 249, 0.96),
                                        borderRadius: BorderRadius.circular(16),
                                        border: Border.all(
                                          color: const Color.fromRGBO(255, 255, 255, 0.58),
                                        ),
                                      ),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          const Row(
                                            children: [
                                              Icon(
                                                Icons.person_outline,
                                                size: 20,
                                                color: Color.fromRGBO(69, 0, 132, 1),
                                              ),
                                              SizedBox(width: 8),
                                              Text(
                                                'Account Overview',
                                                style: TextStyle(
                                                  fontWeight: FontWeight.w700,
                                                  fontSize: 18,
                                                  color: Color.fromRGBO(35, 35, 35, 1),
                                                ),
                                              ),
                                            ],
                                          ),
                                          const SizedBox(height: 14),
                                          _infoRow(
                                            label: 'Username',
                                            value: (username == null || username!.isEmpty)
                                                ? 'Not set'
                                                : username!,
                                          ),
                                          const SizedBox(height: 12),
                                          _infoRow(
                                            label: 'Email',
                                            value: (user.email == null || user.email!.isEmpty)
                                                ? 'Not set'
                                                : user.email!,
                                          ),
                                          const SizedBox(height: 12),
                                          _infoRow(
                                            label: 'Saved Addresses',
                                            value: '${savedAddresses.length}',
                                          ),
                                        ],
                                      ),
                                    );

                                    final Widget addressManagerCard = Container(
                                      width: double.infinity,
                                      padding: const EdgeInsets.all(18),
                                      decoration: BoxDecoration(
                                        color: const Color.fromRGBO(247, 247, 249, 0.96),
                                        borderRadius: BorderRadius.circular(16),
                                        border: Border.all(
                                          color: const Color.fromRGBO(255, 255, 255, 0.58),
                                        ),
                                      ),
                                      child: Column(
                                        crossAxisAlignment: CrossAxisAlignment.start,
                                        children: [
                                          const Row(
                                            children: [
                                              Icon(
                                                Icons.home_work_outlined,
                                                size: 20,
                                                color: Color.fromRGBO(69, 0, 132, 1),
                                              ),
                                              SizedBox(width: 8),
                                              Text(
                                                'Manage Addresses',
                                                style: TextStyle(
                                                  fontWeight: FontWeight.w700,
                                                  fontSize: 18,
                                                  color: Color.fromRGBO(35, 35, 35, 1),
                                                ),
                                              ),
                                            ],
                                          ),
                                          const SizedBox(height: 4),
                                          const Text(
                                            'Set your home address and keep multiple saved options.',
                                            style: TextStyle(
                                              color: Color.fromRGBO(95, 95, 95, 1),
                                              fontSize: 13,
                                            ),
                                          ),
                                          const SizedBox(height: 14),
                                          SizedBox(
                                            width: double.infinity,
                                            child: GooglePlaceAutoCompleteTextField(
                                              textEditingController: _addressController,
                                              googleAPIKey: googleApiKey,
                                              inputDecoration: InputDecoration(
                                                labelText: 'Enter Address',
                                                labelStyle: const TextStyle(color: Colors.black),
                                                filled: true,
                                                fillColor: const Color.fromRGBO(255, 255, 255, 1),
                                                border: OutlineInputBorder(
                                                  borderSide: BorderSide.none,
                                                  borderRadius: BorderRadius.circular(14),
                                                ),
                                                floatingLabelBehavior:
                                                    FloatingLabelBehavior.never,
                                              ),
                                              debounceTime: 800,
                                              isLatLngRequired: false,
                                              itemClick: (prediction) {
                                                _addressController.text =
                                                    prediction.description!;
                                              },
                                            ),
                                          ),
                                          const SizedBox(height: 12),
                                          SizedBox(
                                            width: double.infinity,
                                            child: ElevatedButton(
                                              style: ElevatedButton.styleFrom(
                                                backgroundColor:
                                                    const Color.fromRGBO(203, 182, 119, 0.9),
                                                foregroundColor:
                                                    const Color.fromRGBO(30, 30, 30, 1),
                                                minimumSize: const Size.fromHeight(46),
                                                shape: RoundedRectangleBorder(
                                                  borderRadius: BorderRadius.circular(12),
                                                ),
                                                elevation: 0,
                                              ),
                                              onPressed: _updateHomeAddress,
                                              child: const Text(
                                                'Save Home Address',
                                                style: TextStyle(fontWeight: FontWeight.w600),
                                              ),
                                            ),
                                          ),
                                          const SizedBox(height: 14),
                                          const Text(
                                            'Saved Addresses',
                                            style: TextStyle(
                                              fontWeight: FontWeight.w700,
                                              color: Color.fromRGBO(35, 35, 35, 1),
                                            ),
                                          ),
                                          const SizedBox(height: 8),
                                          Expanded(
                                            child: Container(
                                              decoration: BoxDecoration(
                                                color: const Color.fromRGBO(255, 255, 255, 1),
                                                borderRadius: BorderRadius.circular(12),
                                                border: Border.all(
                                                  color: const Color.fromRGBO(224, 224, 230, 1),
                                                ),
                                              ),
                                              child: savedAddresses.isEmpty
                                                  ? const Center(
                                                      child: Text(
                                                        'No saved addresses',
                                                        style: TextStyle(color: Colors.grey),
                                                      ),
                                                    )
                                                  : Scrollbar(
                                                      child: ListView.builder(
                                                        padding:
                                                            const EdgeInsets.symmetric(
                                                          horizontal: 12,
                                                          vertical: 10,
                                                        ),
                                                        itemCount: savedAddresses.length,
                                                        itemBuilder: (context, index) {
                                                          final String addr =
                                                              savedAddresses[index];
                                                          return Padding(
                                                            padding: const EdgeInsets.symmetric(
                                                                vertical: 4),
                                                            child: Row(
                                                              crossAxisAlignment:
                                                                  CrossAxisAlignment.start,
                                                              children: [
                                                                Expanded(
                                                                  child: Text(
                                                                    addr,
                                                                    maxLines: 2,
                                                                    overflow: TextOverflow.ellipsis,
                                                                    style: const TextStyle(
                                                                      fontSize: 15,
                                                                      height: 1.25,
                                                                    ),
                                                                  ),
                                                                ),
                                                                const SizedBox(width: 6),
                                                                IconButton(
                                                                  icon: const Icon(
                                                                    Icons.close,
                                                                    size: 18,
                                                                    color: Colors.red,
                                                                  ),
                                                                  padding: EdgeInsets.zero,
                                                                  constraints:
                                                                      const BoxConstraints(),
                                                                  tooltip: 'Delete',
                                                                  onPressed: () =>
                                                                      _deleteSavedAddress(addr),
                                                                ),
                                                              ],
                                                            ),
                                                          );
                                                        },
                                                      ),
                                                    ),
                                            ),
                                          ),
                                        ],
                                      ),
                                    );

                                    return SingleChildScrollView(
                                      child: Padding(
                                        padding:
                                            const EdgeInsets.symmetric(vertical: 8),
                                        child: isWide
                                            ? SizedBox(
                                                height: mediaQuery.size.height -
                                                    topPanelInset -
                                                    bottomPanelInset -
                                                    16,
                                                child: Row(
                                                  crossAxisAlignment:
                                                      CrossAxisAlignment.stretch,
                                                  children: [
                                                    Expanded(flex: 1, child: profileCard),
                                                    const SizedBox(width: 20),
                                                    Expanded(
                                                      flex: 2,
                                                      child: addressManagerCard,
                                                    ),
                                                  ],
                                                ),
                                              )
                                            : Column(
                                                children: [
                                                  profileCard,
                                                  const SizedBox(height: 16),
                                                  SizedBox(
                                                    height: 500,
                                                    child: addressManagerCard,
                                                  ),
                                                ],
                                              ),
                                      ),
                                    );
                                  },
                                ),
                              ),
                            )
                          : const Align(
                              alignment: Alignment.topCenter,
                              child: Text('User not authenticated'),
                            ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _infoRow({required String label, required String value}) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
      decoration: BoxDecoration(
        color: const Color.fromRGBO(255, 255, 255, 1),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color.fromRGBO(226, 226, 232, 1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            label,
            style: const TextStyle(
              color: Color.fromRGBO(95, 95, 95, 1),
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            value,
            style: const TextStyle(
              color: Color.fromRGBO(30, 30, 30, 1),
              fontSize: 14,
              fontWeight: FontWeight.w600,
            ),
          ),
        ],
      ),
    );
  }

}
