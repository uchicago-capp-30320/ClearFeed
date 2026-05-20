# ClearFeed User Testing Scenarios

This document outlines end-to-end user testing scenarios for the **ClearFeed web application** and **ClearFeed Capture browser extension**.

For each scenario:

- Follow the **Test Instructions**
- Compare against the **Expected Behavior**
- Complete the **Test Result** section

---

# Browser Extension Scenarios

---

## 1. Empty Upload

### Test Instructions
1. Open the **ClearFeed Capture** extension page.
2. Make sure you are logged into the main ClearFeed application.
3. Without capturing any feed data (`Items = 0`), click **"To ClearFeed"**.

### Expected Behavior
- Upload should be blocked.
- User should receive an informative message indicating **no data is available to upload**.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 2. Upload Failure — Not Logged In

### Test Instructions
1. Open the **ClearFeed Capture** extension page.
2. Make sure you are **not logged in** to the ClearFeed web application.
3. Click **"To ClearFeed"**.

### Expected Behavior
- Upload should be blocked.
- User should receive an informative **"not logged in"** message.
- Message should contain a direct link to the ClearFeed login page.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 3. Feed Data Collection - Active

### Test Instructions
1. Open the **ClearFeed Capture** extension page.
2. Confirm **"Active"** is toggled on.
3. Navigate to **X/Twitter**.
4. Scroll through the feed for several seconds.
5. Return to the extension.

### Expected Behavior
- Extension should display a **nonzero Items count**.
- This indicates successful feed capture.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 4. Feed Data Collection — Inactive

### Test Instructions
1. Open the **ClearFeed Capture** extension page.
2. Confirm **"Active"** is toggled **off**.
3. Navigate to **X/Twitter**.
4. Scroll through the feed for several seconds.
5. Return to the extension.

### Expected Behavior
- Extension should continue displaying **0 Items**.
- No feed data should be captured while the extension is inactive.
- This confirms user feed privacy when capture is disabled.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 5. Feed Data Deletion

### Test Instructions
1. Open **ClearFeed Capture**.
2. Ensure **"Active"** is toggled on.
3. Navigate to **X/Twitter** and scroll briefly.
4. Return to the extension.
5. Confirm `Items > 0`.
6. Click **"Delete"**.

### Expected Behavior
- `Items` count should immediately return to **0**.
- Captured data should be discarded.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 6. Successful Upload

### Test Instructions
1. Open **ClearFeed Capture**.
2. Ensure **"Active"** is enabled.
3. Navigate to **X/Twitter** and scroll briefly.
4. Return to the extension.
5. Confirm `Items > 0`.
6. Click **"To ClearFeed"**.

### Expected Behavior
- Extension should display **"Uploading"**.
- After several seconds, message should change to **"Upload complete"**.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 7. Navigate to ClearFeed

### Test Instructions
1. Open the **ClearFeed Capture** extension page.
2. Click **"View ClearFeed Report"**.

### Expected Behavior
- Browser should navigate directly to the ClearFeed home page.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

# ClearFeed Authentication Scenarios

---

## 8. Signup — Invalid Email

### Test Instructions
1. Navigate to **Signup**.
2. Enter an invalid email:
   - Missing `@`
   - OR missing text after `@`
3. Enter password + confirmation.
4. Click **"Create Account"**.

### Expected Behavior
- User remains on signup page.
- Relevant email validation error should appear.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 9. Signup — Invalid Password

### Test Instructions
1. Navigate to **Signup**.
2. Enter valid email.
3. Enter invalid password:
   - Fewer than 8 characters
   - OR entirely numeric
4. Click **"Create Account"**.

### Expected Behavior
- User remains on signup page.
- Relevant password validation error should appear.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 10. Signup — Passwords Do Not Match

### Test Instructions
1. Navigate to **Signup**.
2. Enter valid email.
3. Enter valid password.
4. Enter different password confirmation.
5. Click **"Create Account"**.

### Expected Behavior
- User remains on signup page.
- Password mismatch error should appear.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 11. Signup — Valid

### Test Instructions
1. Navigate to **Signup**.
2. Enter valid email.
3. Enter matching valid passwords.
4. Click **"Create Account"**.

### Expected Behavior
- User should be logged in automatically.
- User should be redirected to the **Onboarding** page.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 12. Login — Empty Field

### Test Instructions
1. Navigate to **Login**.
2. Leave either email or password blank.
3. Click **"Sign In"**.

### Expected Behavior
- User remains on login page.
- Browser displays **"Please fill out this field."**

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 13. Login — Invalid Credentials

### Test Instructions
1. Navigate to **Login**.
2. Enter incorrect email/password combination.
3. Click **"Sign In"**.

### Expected Behavior
- User remains on login page.
- Generic invalid credentials message appears.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 14. Login — Valid

### Test Instructions
1. Navigate to **Login**.
2. Enter valid credentials.
3. Click **"Sign In"**.

### Expected Behavior
- User is logged in.
- User is redirected to ClearFeed home page.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 15. Logout

### Test Instructions
1. Confirm user is logged in.
2. Click **"Logout"**.

### Expected Behavior
- User is logged out immediately.
- User is redirected to login page.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

# ClearFeed Navigation Scenarios

---

## 16. Navigation Access — Logged Out

### Test Instructions
1. Ensure user is logged out.

### Expected Behavior
User can access:

- Welcome
- Privacy
- Onboarding
- Signup
- Login

Clicking **User Profile** should redirect to Login.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 17. Navigation Access — Logged In

### Test Instructions
1. Ensure user is logged in.

### Expected Behavior
User can access:

- Welcome
- User Profile
- Privacy
- Onboarding
- Feed Summary
- Signup
- Login

All navigation tabs should route correctly.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

# ClearFeed Visualization Scenarios

---

## 18. Feed Summary — Topic Distribution

### Test Instructions
1. Log into ClearFeed.
2. Navigate to **Feed Summary**.
3. Scroll to **Topic Distribution**.

### Expected Behavior

**With Data**
- Top 5 topic bar chart appears.
- Hover displays exact percentages.

**Without Data**
- Visualization is blank or empty.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 19. Feed Summary — Promoted Tweets

### Test Instructions
1. Log into ClearFeed.
2. Navigate to **Feed Summary**.
3. Scroll to **Promoted Tweets**.

### Expected Behavior

**With Data**
- Visualization appears showing:
  - Total tweets ingested
  - Proportion promoted
  - Top 5 promoted accounts

**Without Data**
- Visualization is blank or empty.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 20. Feed Summary — Sentiment Analysis

### Test Instructions
1. Log into ClearFeed.
2. Navigate to **Feed Summary**.
3. Scroll to **Sentiment Analysis**.

### Expected Behavior

**With Data**
- Sentiment barometer appears.
- Breakdown by sentiment category.
- Overall sentiment score + description shown.

**Without Data**
- Visualization is blank or empty.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

## 21. Feed Summary — Word Frequency Cloud

### Test Instructions
1. Log into ClearFeed.
2. Navigate to **Feed Summary**.
3. Scroll to **Word Frequency Cloud**.

### Expected Behavior

**With Data**
- Word cloud displays common word tokens.
- Hover displays frequency counts.

**Without Data**
- Visualization is blank or empty.

### Test Result
- [ ] Pass  
- [ ] Fail  

**Tester Feedback / Notes:**  
__________________________________________________  
__________________________________________________

---

# Testing Summary

| Scenario | Pass | Fail | Notes |
|---|---|---|---|
| Extension | ☐ | ☐ | |
| Authentication | ☐ | ☐ | |
| Navigation | ☐ | ☐ | |
| Visualizations | ☐ | ☐ | |

---

**Overall Testing Notes / Issues Identified**

__________________________________________________  

__________________________________________________  

__________________________________________________