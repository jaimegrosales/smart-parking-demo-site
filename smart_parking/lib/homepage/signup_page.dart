// Written by Tim Hudson - Last Updated 4/1/2025
// Written with the assistance of Openstack, Google Codelabs and ChatGPT

// This code is responsible for the signup page that allows a user to create an account with a username, email and password
// This code takes the entered data and stores it in the firebase
// The username and email are store in the database, the email in the database and the authentication and the password is just stored in the authentication

// This page is accessed through the account tab

// Import the needed package
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:smart_parking/homepage/account_page.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

// signup is stateful
class Signup extends StatefulWidget {
  const Signup({super.key});

  @override
  _SignupState createState() => _SignupState();
}

class _SignupState extends State<Signup> {
  // Controllers for the text fields
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _usernameController = TextEditingController();

  bool _isObscured = true;
  String _password = "";

  // build the UI for the app
  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);
    final bool isWide = mediaQuery.size.width >= 900;
    final double horizontalPadding =
        isWide ? mediaQuery.size.width * 0.16 : mediaQuery.size.width * 0.06;

    return Scaffold(
      backgroundColor: Colors.transparent,
      extendBodyBehindAppBar: true,
      extendBody: true,
      resizeToAvoidBottomInset: true,
      appBar: AppBar(
        title: Text(
          'Register Account',
          style: GoogleFonts.montserrat(fontWeight: FontWeight.w500),
        ),
        backgroundColor: Colors.transparent,
        foregroundColor: const Color.fromARGB(255, 255, 255, 255),
        elevation: 0,
        scrolledUnderElevation: 0,
        shadowColor: Colors.transparent,
        surfaceTintColor: Colors.transparent,
      ),
      body: SizedBox.expand(
        child: Container(
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
          child: SafeArea(
            child: SingleChildScrollView(
              padding: EdgeInsets.fromLTRB(
                horizontalPadding,
                kToolbarHeight + 24,
                horizontalPadding,
                24,
              ),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 620),
                  child: Container(
                    padding: const EdgeInsets.all(22),
                    decoration: BoxDecoration(
                      color: const Color.fromRGBO(247, 247, 249, 0.96),
                      borderRadius: BorderRadius.circular(18),
                      border: Border.all(
                        color: const Color.fromRGBO(255, 255, 255, 0.58),
                      ),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Create Your Account',
                          style: TextStyle(
                            color: Color.fromRGBO(35, 35, 35, 1),
                            fontSize: 26,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 6),
                        const Text(
                          'Sign up to save addresses and get parking predictions faster.',
                          style: TextStyle(
                            color: Color.fromRGBO(95, 95, 95, 1),
                            fontSize: 14,
                          ),
                        ),
                        const SizedBox(height: 22),
                        _usernameField(),
                        const SizedBox(height: 16),
                        _emailField(),
                        const SizedBox(height: 16),
                        _passwordField(),
                        const SizedBox(height: 12),
                        _passwordRequirements(),
                        const SizedBox(height: 22),
                        _signupButton(context),
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

  // Username field
  Widget _usernameField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Username',
          style: TextStyle(
            color: Color.fromRGBO(45, 45, 45, 1),
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 6),
        TextField(
          controller: _usernameController,
          decoration: InputDecoration(
            filled: true,
            hintText: 'Enter your username',
            hintStyle: const TextStyle(
              color: Color(0xff6A6A6A),
              fontSize: 14,
            ),
            fillColor: const Color.fromRGBO(247, 247, 249, 1),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: const BorderSide(
                color: Color.fromRGBO(220, 220, 226, 1),
              ),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: const BorderSide(
                color: Color.fromRGBO(220, 220, 226, 1),
              ),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: const BorderSide(
                color: Color.fromRGBO(69, 0, 132, 1),
              ),
            ),
          ),
        ),
      ],
    );
  }

  // Email field
  Widget _emailField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Email Address',
          style: TextStyle(
            color: Color.fromRGBO(45, 45, 45, 1),
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 6),
        TextField(
          controller: _emailController,
          decoration: InputDecoration(
            filled: true,
            hintText: 'example@test.com',
            hintStyle: const TextStyle(
                color: Color(0xff6A6A6A),
                fontWeight: FontWeight.normal,
                fontSize: 14),
            fillColor: const Color(0xffF7F7F9),
            border: OutlineInputBorder(
                borderSide: const BorderSide(
                  color: Color.fromRGBO(220, 220, 226, 1),
                ),
                borderRadius: BorderRadius.circular(14)),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: const BorderSide(
                color: Color.fromRGBO(220, 220, 226, 1),
              ),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: const BorderSide(
                color: Color.fromRGBO(69, 0, 132, 1),
              ),
            ),
          ),
        ),
      ],
    );
  }

  // Password field with obscure toggle and onChange to update password requirements.
  Widget _passwordField() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Password',
          style: TextStyle(
            color: Color.fromRGBO(45, 45, 45, 1),
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 6),
        TextField(
          controller: _passwordController,
          obscureText: _isObscured,
          onChanged: (value) {
            setState(() {
              _password = value;
            });
          },
          decoration: InputDecoration(
            filled: true,
            fillColor: const Color(0xffF7F7F9),
            border: OutlineInputBorder(
              borderSide: const BorderSide(
                color: Color.fromRGBO(220, 220, 226, 1),
              ),
              borderRadius: BorderRadius.circular(14),
            ),
            enabledBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: const BorderSide(
                color: Color.fromRGBO(220, 220, 226, 1),
              ),
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(14),
              borderSide: const BorderSide(
                color: Color.fromRGBO(69, 0, 132, 1),
              ),
            ),
            suffixIcon: IconButton(
              icon: Icon(
                _isObscured ? Icons.visibility_off : Icons.visibility,
                color: Colors.grey,
              ),
              onPressed: () {
                setState(() {
                  _isObscured = !_isObscured;
                });
              },
            ),
          ),
        ),
      ],
    );
  }

  // Password requirements container that shows real-time validation.
  Widget _passwordRequirements() {
    bool hasUpperCase = _password.contains(RegExp(r'[A-Z]'));
    bool hasLowerCase = _password.contains(RegExp(r'[a-z]'));
    bool hasNumber = _password.contains(RegExp(r'[0-9]'));
    bool hasMinLength = _password.length >= 8;

    return Container(
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color.fromRGBO(255, 255, 255, 1),
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: const Color.fromRGBO(224, 224, 230, 1)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _passwordRequirement("At least 8 characters", hasMinLength),
          _passwordRequirement("At least one uppercase letter", hasUpperCase),
          _passwordRequirement("At least one lowercase letter", hasLowerCase),
          _passwordRequirement("At least one number", hasNumber),
        ],
      ),
    );
  }

  Widget _passwordRequirement(String text, bool met) {
    return Row(
      children: [
        Icon(
          met ? Icons.check_circle : Icons.cancel,
          color: met ? Colors.green : Colors.red,
          size: 18,
        ),
        const SizedBox(width: 8),
        Text(
          text,
          style: TextStyle(
            color: met
                ? const Color.fromRGBO(24, 120, 72, 1)
                : const Color.fromRGBO(185, 42, 42, 1),
          ),
        ),
      ],
    );
  }

  void showCustomSnackBar(BuildContext context, String message) {
    final overlay = Overlay.of(context);
    final overlayEntry = OverlayEntry(
      builder: (context) => Positioned(
        top: MediaQuery.of(context).size.height / 2 - 40, // Center vertically
        left: 20,
        right: 20,
        child: Material(
          color: Colors.transparent,
          child: Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: Colors.black87,
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              message,
              style: const TextStyle(color: Colors.white),
              textAlign: TextAlign.center,
            ),
          ),
        ),
      ),
    );

    overlay.insert(overlayEntry);

    // Remove after 2 seconds
    Future.delayed(const Duration(seconds: 2), () {
      overlayEntry.remove();
    });
  }

  // Signup button that integrates Firebase Authentication and Firestore.
  Widget _signupButton(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color.fromRGBO(203, 182, 119, 0.9),
          foregroundColor: const Color.fromRGBO(30, 30, 30, 1),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          minimumSize: const Size(double.infinity, 52),
          elevation: 0,
        ),
        onPressed: () async {
          if (_usernameController.text.isEmpty ||
              _emailController.text.isEmpty ||
              _passwordController.text.isEmpty) {
            showCustomSnackBar(context, 'Please fill all fields.');
            return;
          }
          try {
            // Create a new user account with Firebase Authentication
            UserCredential userCredential =
                await FirebaseAuth.instance.createUserWithEmailAndPassword(
              email: _emailController.text,
              password: _passwordController.text,
            );
            // Get the userID
            String userId = userCredential.user!.uid;

            // Save additional user information in Firestore
            await FirebaseFirestore.instance
                .collection('users')
                .doc(userId)
                .set({
              'username': _usernameController.text,
              'email': _emailController.text,
              'userID': userId,
            });

            Navigator.pushReplacement(
              context,
              MaterialPageRoute(
                builder: (context) => const AccountPage(),
              ),
            );
          } catch (e) {
            showCustomSnackBar(context, 'Error creating account.');
          }
        },
        child: const Text(
          'Sign Up',
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }

}
