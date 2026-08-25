# Key Beta 1 Sequences

## 1. Private onboarding

Web registration
 -> Beta approval
 -> approval email
 -> bot deep link
 -> Telegram /start
 -> Telegram Adapter
 -> BetaAccessService
 -> approved account lookup
 -> identity binding
 -> welcome response

## 2. /world

Telegram /world
 -> Telegram Adapter
 -> WorldService
 -> assigned Worlds
 -> Telegram response

## 3. /status

Telegram /status
 -> Telegram Adapter
 -> BetaStatusService
 -> account + Worlds + classroom + issue summary
 -> Telegram response

## 4. Report issue

Telegram
 -> fixed issue link
 -> EasyChatBot web application
 -> issue form
 -> IssueManagementService
 -> PostgreSQL
 -> reference number

## 5. Announcement channel

Administrator
 -> Telegram announcement channel
 -> Beta users read/react

The bot does not publish or administer the announcement channel.
