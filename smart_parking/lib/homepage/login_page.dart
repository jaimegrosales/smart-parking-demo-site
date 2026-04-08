// Written by Tim Hudson - Last Updated 4/1/2025
// Written with the assistance of Openstack, Google Codelabs and ChatGPT

// This code is responsible for the login feature to allow users full functiuonality from the app
// This code has allows the user to sign in with an email and a password. It also allows the user to reset their password oif they have forgotten it

// This page is accessed through the account tab

// Import the needed packages

import 'package:firebase_auth/firebase_auth.dart';
import 'package:smart_parking/homepage/signup_page.dart';
import 'package:smart_parking/main.dart';
import 'package:smart_parking/services/auth_service.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:smart_parking/homepage/home_page.dart';

// Import your HomePage or starting page

class Login extends StatefulWidget {
  const Login({super.key});

  @override
  _LoginState createState() => _LoginState();
}

class _LoginState extends State<Login> {
  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();

  bool _isObscured = true; // Password visibility state

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final mediaQuery = MediaQuery.of(context);
    final double screenWidth = mediaQuery.size.width;
    final bool isNarrow = screenWidth < 420;
    final double horizontalPadding = screenWidth < 600 ? 18.0 : (screenWidth < 1000 ? 44.0 : 90.0);
    return Scaffold(
      backgroundColor: const Color.fromRGBO(0, 0, 0, 1),
      resizeToAvoidBottomInset: true,
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
        child: SafeArea(
          child: LayoutBuilder(
            builder: (context, constraints) {
              return SingleChildScrollView(
                padding: EdgeInsets.fromLTRB(horizontalPadding, 100, horizontalPadding, 22),
                child: ConstrainedBox(
                  constraints: BoxConstraints(minHeight: constraints.maxHeight - 42),
                  child: Align(
                    alignment: Alignment.topCenter,
                    child: ConstrainedBox(
                      constraints: const BoxConstraints(maxWidth: 680),
                      child: Column(
                        mainAxisAlignment: MainAxisAlignment.start,
                        children: [
                          _buildImage(),
                          const SizedBox(height: 8),
                          Text(
                            'Smart Parking Assistant',
                            style: GoogleFonts.montserrat(
                              color: const Color.fromRGBO(236, 236, 240, 1),
                              fontSize: isNarrow ? 31 : 40,
                              fontWeight: FontWeight.w500,
                              letterSpacing: -0.4,
                            ),
                            textAlign: TextAlign.center,
                          ),
                          const SizedBox(height: 22),
                          Container(
                            padding: EdgeInsets.all(isNarrow ? 16 : 22),
                            decoration: BoxDecoration(
                              color: const Color.fromRGBO(247, 247, 249, 0.96),
                              borderRadius: BorderRadius.circular(20),
                              border: Border.all(
                                color: const Color.fromRGBO(255, 255, 255, 0.55),
                              ),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'Welcome Back',
                                  style: TextStyle(
                                    color: Color.fromRGBO(28, 28, 28, 1),
                                    fontSize: 22,
                                    fontWeight: FontWeight.w700,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                const Text(
                                  'Sign in to access your saved addresses and parking tools.',
                                  style: TextStyle(
                                    color: Color.fromRGBO(93, 93, 93, 1),
                                    fontSize: 14,
                                  ),
                                ),
                                const SizedBox(height: 18),
                                _emailAddress(),
                                const SizedBox(height: 14),
                                _password(),
                                const SizedBox(height: 4),
                                _forgotPasswordButton(context),
                                const SizedBox(height: 10),
                                _signin(context),
                                const SizedBox(height: 12),
                                _signup(context),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              );
            },
          ),
        ),
      ),
    );
  }

  Widget _emailAddress() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Email Address',
          style: TextStyle(
            color: Color.fromRGBO(45, 45, 45, 1),
            fontSize: 13,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 6),
        TextField(
          controller: _emailController,
          style: const TextStyle(fontSize: 15),
          decoration: InputDecoration(
            isDense: true,
            contentPadding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
            filled: true,
            hintText: 'example@test.com',
            hintStyle: const TextStyle(
              color: Color.fromRGBO(106, 106, 106, 1),
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

  Widget _password() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Password',
          style: TextStyle(
            color: Color.fromRGBO(45, 45, 45, 1),
            fontSize: 13,
            fontWeight: FontWeight.w600,
          ),
        ),
        const SizedBox(height: 6),
        TextField(
          controller: _passwordController,
          obscureText: _isObscured,
          style: const TextStyle(fontSize: 15),
          decoration: InputDecoration(
            isDense: true,
            contentPadding: const EdgeInsets.symmetric(vertical: 14, horizontal: 12),
            filled: true,
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
            suffixIcon: IconButton(
              icon: Icon(
                _isObscured ? Icons.visibility_off : Icons.visibility,
                color: const Color.fromRGBO(158, 158, 158, 1),
              ),
              onPressed: () {
                setState(() {
                  _isObscured = !_isObscured;
                });
              },
              splashRadius: 18,
            ),
          ),
          onSubmitted: (_) async {
            await AuthService().signin(
              email: _emailController.text,
              password: _passwordController.text,
              context: context,
            );
          },
        ),
      ],
    );
  }

  Widget _forgotPasswordButton(BuildContext context) {
    return Align(
      alignment: Alignment.centerRight,
      child: TextButton(
        onPressed: () => _resetPassword(context),
        child: const Text(
          'Forgot Password?',
          style: TextStyle(
            color: Color.fromRGBO(203, 182, 119, 1),
            fontSize: 13,
            fontWeight: FontWeight.w500,
          ),
        ),
      ),
    );
  }

  Future<void> _resetPassword(BuildContext context) async {
    if (_emailController.text.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter your email address')),
      );
      return;
    }

    try {
      await FirebaseAuth.instance
          .sendPasswordResetEmail(email: _emailController.text);
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Password reset link sent to your email')),
      );
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error: ${e.toString()}')),
      );
    }
  }

  Widget _signin(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      child: ElevatedButton(
        style: ElevatedButton.styleFrom(
          backgroundColor: const Color.fromRGBO(203, 182, 119, 0.95),
          foregroundColor: const Color.fromRGBO(29, 29, 29, 1),
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
          ),
          minimumSize: const Size(double.infinity, 50),
          elevation: 0,
        ),
        onPressed: () async {
          await AuthService().signin(
            email: _emailController.text,
            password: _passwordController.text,
            context: context,
          );
        },
        child: const Text(
          'Sign In',
          style: TextStyle(fontSize: 17, fontWeight: FontWeight.w600),
        ),
      ),
    );
  }

  Widget _signup(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 4),
      child: RichText(
        textAlign: TextAlign.center,
        text: TextSpan(
          children: [
            const TextSpan(
              text: "New User? ",
              style: TextStyle(
                  color: Color.fromRGBO(82, 82, 82, 1), fontSize: 13),
            ),
            TextSpan(
              text: "Create Account",
              style: const TextStyle(
                  color: Color.fromRGBO(203, 182, 119, 1), fontSize: 13, fontWeight: FontWeight.w500),
              recognizer: TapGestureRecognizer()
                ..onTap = () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (context) => const Signup()),
                  );
                },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildImage() {
    final double screenWidth = MediaQuery.of(context).size.width;
    // Keep the logo generally larger while staying responsive across devices.
    final double logoWidth = (screenWidth * 0.9).clamp(320.0, 520.0).toDouble();
    return Image.asset(
      'assets/images/JMU-Logo-RGB-vert-white.png',
      width: logoWidth,
      fit: BoxFit.contain,
    );
  }
}
