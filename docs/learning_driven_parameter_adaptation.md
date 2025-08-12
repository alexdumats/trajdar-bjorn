# Learning-Driven Parameter Adaptation System

This document describes the learning-driven parameter adaptation system implemented in the trading platform. The system enables iterative, learning-driven parameter adaptation based on real outcomes, especially addressing situations where trades are blocked or paper trading does not translate to live execution due to strict risk controls.

## Overview

The learning-driven parameter adaptation system consists of several components:

1. **Blocked Trade Tracking**: Tracks and logs trades that are blocked due to risk parameters
2. **Slack Notifications**: Sends notifications to Slack when trades are blocked
3. **Learning Sessions**: Scheduled periods where risk parameters are relaxed to allow for exploration
4. **Parameter Optimization**: Uses data from blocked trades and learning sessions to optimize parameters
5. **Slack Command Interface**: Allows authorized users to override risk blocks and manage learning sessions
6. **Backup System**: Ensures all parameter changes are backed up and can be restored if needed

## Blocked Trade Tracking

The system tracks trades that are blocked due to risk parameters. This information is stored in a database table called `blocked_trades` and includes:

- Timestamp
- Symbol
- Signal (BUY/SELL)
- Block reason
- RSI value
- Price
- Confidence
- Risk level
- Additional data

This data is used to identify patterns in blocked trades and inform parameter optimization.

## Slack Notifications

When a trade is blocked, a notification is sent to the `#risk-blocked` Slack channel. The notification includes:

- Signal (BUY/SELL)
- Reason for the block
- Symbol
- Price
- RSI value
- Confidence
- Risk level
- Timestamp

This allows traders to monitor blocked trades in real-time and take action if needed.

## Learning Sessions

Learning sessions are scheduled periods where risk parameters are temporarily relaxed to allow for exploration. During a learning session:

1. Original parameters are backed up
2. Parameters are relaxed (lower confidence threshold, higher position size, etc.)
3. All trades executed during the session are tagged for analysis
4. After the session ends, original parameters are restored
5. Session results are analyzed and stored

Learning sessions can be started and stopped manually via Slack commands or scheduled automatically.

### Learning Session Parameters

The following parameters are relaxed during a learning session:

- `min_confidence`: Reduced by 10-20%
- `max_position_size`: Increased by 10-30%
- `stop_loss_pct`: Increased by 10-20%
- `take_profit_pct`: Decreased by 10-20%

### Learning Session Analysis

After a learning session, the system analyzes the results:

- Total trades executed
- Successful vs. unsuccessful trades
- Win rate
- Total PnL
- Average PnL
- Maximum profit and loss

Based on this analysis, the system generates recommendations for parameter adjustments.

## Parameter Optimization

The parameter optimizer uses data from blocked trades and learning sessions to optimize trading parameters. It considers:

- Patterns in blocked trades
- Performance during learning sessions
- Overall trading performance

The optimizer can be triggered manually or automatically when certain conditions are met (e.g., high number of blocked trades, poor performance).

## Slack Command Interface

The system provides a Slack command interface for authorized users to:

- Override risk blocks for individual trades
- Start and stop learning sessions
- View learning session status
- View blocked trade statistics
- Update parameters

### Available Commands

- `/param override <symbol> <side> <reason>` - Override risk block for a trade
- `/param learning start [duration_minutes]` - Start a learning session
- `/param learning stop` - Stop a learning session
- `/param learning status` - Check learning session status
- `/param show <parameter>` - Show current parameter value
- `/param set <parameter> <value>` - Set parameter to new value
- `/param reset <parameter>` - Reset parameter to default value

## Backup System

All parameter changes are backed up to ensure they can be restored if needed. The backup system:

1. Creates a backup of the current configuration before any change
2. Stores backups in a dedicated directory with timestamps
3. Logs all parameter changes to a database and file
4. Provides an API to view backup history and restore previous configurations

## API Endpoints

The system provides several API endpoints for managing the learning-driven parameter adaptation:

### Parameter Optimizer Service

- `POST /start-learning-session` - Start a learning session
- `POST /end-learning-session` - End a learning session
- `GET /learning-session-status` - Get current learning session status
- `GET /blocked-trades` - Get blocked trade statistics
- `GET /learning-sessions` - Get learning session history
- `POST /backup-configuration` - Create a backup of current configuration
- `GET /configuration-backups` - Get configuration backup history
- `GET /parameter-changes` - Get parameter change history

### Slack Integration Service

- `POST /process-command` - Process Slack commands
- `POST /send-message` - Send message to Slack

## Usage Examples

### Starting a Learning Session

To start a learning session for 60 minutes:

```
/param learning start 60
```

### Overriding a Risk Block

To override a risk block for a BUY signal on BTCUSDC:

```
/param override BTCUSDC BUY strategic_opportunity
```

### Viewing Blocked Trade Statistics

To view blocked trade statistics, use the API endpoint:

```
GET /blocked-trades
```

## Best Practices

1. **Start with Short Learning Sessions**: Begin with short learning sessions (30-60 minutes) to minimize risk
2. **Monitor Learning Sessions**: Always monitor learning sessions closely
3. **Review Results**: Review learning session results before making permanent parameter changes
4. **Document Overrides**: Always provide a clear reason when overriding risk blocks
5. **Regular Backups**: Regularly backup configurations before making changes

## Troubleshooting

### Learning Session Not Starting

If a learning session fails to start, check:

1. Is another learning session already active?
2. Is the system in cooldown period after a previous session?
3. Are there any errors in the logs?

### Risk Override Not Working

If a risk override fails, check:

1. Are you an authorized user?
2. Is the symbol valid?
3. Is the side valid (BUY/SELL)?
4. Are there any errors in the logs?

## Conclusion

The learning-driven parameter adaptation system provides a structured approach to iteratively improve trading parameters based on real outcomes. By tracking blocked trades, implementing learning sessions, and providing a command interface for overrides, the system enables the trading platform to learn and adapt over time.