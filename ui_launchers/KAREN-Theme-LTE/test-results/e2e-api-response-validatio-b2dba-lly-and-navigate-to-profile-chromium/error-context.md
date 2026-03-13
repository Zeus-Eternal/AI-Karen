# Page snapshot

```yaml
- generic [ref=e3]:
  - generic [ref=e4]:
    - heading "Karen AI" [level=1] [ref=e5]
    - paragraph [ref=e6]: Sign in to your account
  - generic [ref=e7]:
    - generic [ref=e8]:
      - heading "Login" [level=3] [ref=e9]
      - paragraph [ref=e10]: Enter your credentials to access the application
    - generic [ref=e11]:
      - generic [ref=e12]:
        - generic [ref=e13]:
          - text: Email Address
          - textbox "Email Address" [ref=e14]:
            - /placeholder: Enter your email
        - generic [ref=e15]:
          - text: Password
          - generic [ref=e16]:
            - textbox "Password" [ref=e17]:
              - /placeholder: Enter your password
            - button "Show password" [ref=e18] [cursor=pointer]:
              - img [ref=e19]
        - button "Sign In" [disabled]
      - generic [ref=e22]:
        - heading "Test Credentials" [level=3] [ref=e23]
        - generic [ref=e24]:
          - paragraph [ref=e25]:
            - strong [ref=e26]: "Email:"
            - text: testuser@example.com
          - paragraph [ref=e27]:
            - strong [ref=e28]: "Password:"
            - text: testpassword123
```