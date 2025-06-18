# Message formats

The basic message format in `message.py` is a JSON object with fields that represent the properties of a message. Typically, these fields include:

- `source_type`: Type of the message source, e.g., 'email', 'system', 'service', etc.
- `source_id`: Unique ID of the message source, e.g. `Message-Id` header in emails, used to detect duplicates
- `subject`: The subject or title of the message.
- `content`: The content of the message. For emails, the entire email is stored here, including headers, HTML and text parts and attachments.
- `timestamp`: ISO-date of the message
- `metadata`: Additional metadata (optional).

## GitHub messages

GitHub messages are processed by the `GitHubMailAgent` which accepts messages of source type `email` and the `From` header containing `@github.com`. Depending on the content, it preprocesses the incoming messages and converts them into different new messages on the event bus. Default prefix for GitHub messages is `github`.

### \<prefix>.ci_activity

For CI activities, i.e., workflow failure reports, messages of source type "ci_activity" are created.

The metadata contains the following entries:
- `repository_url`: The URL of the repository where the CI activity occurred.
- `repository`: The name of the repository where the CI activity occurred.
- `workflow`: The name of the workflow.
- `results`: The URL to view the results of the CI activity.

### \<prefix>.pr_comment, <prefix>.issue_comment

For comments on issues or pull requests, messages of source type "pr_comment" or "issue_comment" are created. These messages summarize the comment content and the context in which it was made.

Message metadata will include:
- `repository_url`: The URL of the repository where the comment was made.
- `repository`: The name of the repository where the comment was made.
- `content`: The content of the comment, which may include text, code snippets, or links.
- `author`: The username of the author of the comment.
- `pr`: The pull request number if the comment was made on a pull request.
- `issue`: The issue number if the comment was made on an issue.
- `url`: The URL of the issue or pull request where the comment was made.

### \<prefix>.security_alert

For security alerts (f.x. Dependabot weekly digest), messages of source type "security_alert" are created. These messages summarize the dependencies that require updates.

Message metadata will include:
- `repository_url`: The URL of the repository where the alert was triggered.
- `repository`: The name of the repository where the alert was triggered.
- `dependency`: The name of the vulnerable dependency.
- `vulnerable_version`: The version of the dependency that is vulnerable.
- `upgrade_to`: The version to which the dependency should be upgraded.
- `defined_in`: The file where the dependency is defined.
- `vulnerabilities`: A description of the vulnerabilities associated with the dependency.
- `suggested_update`: A suggested update for the dependency.
