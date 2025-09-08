I'll get a PR ready, but here's what I found: Domain alias resolution was happening for provider selection, but the account_id parameter was never normalized to use the primary domain before database lookups.

Before:
1. User configured primary domain `primary.com` in config
2. Hello key stored as `user@primary.com/hello`
3. User attempts login with alias `user@alias.com`
4. `find_provider!` correctly resolved `alias.com` → `primary.com`
5. `account_id` remained `user@alias.com` when passed to provider methods
6. `fetch_hello_key()` looked for `user@alias.com/hello` instead of `user@primary.com/hello`
7. Database lookup failed → "Hello key missing" error

Proposed fix:
`src/common/src/idprovider/himmelblau.rs`

1. Added `normalize_account_id` helper method (lines 248-258):
```
async fn normalize_account_id(&self, account_id: &str) -> String {
    match split_username(account_id) {
        Some((username, domain)) => {
            let mut cfg = self.config.write().await;
            match cfg.get_primary_domain_from_alias(domain).await {
                Some(primary_domain) => format!("{}@{}", username, primary_domain),
                None => account_id.to_string(),
            }
        }
        None => account_id.to_string(),
    }
}
```

2. Updated all authentication methods to normalize `account_id` before passing it to the provider:
  - `unix_user_offline_auth_init`
  - `unix_user_offline_auth_step`
  - `unix_user_online_auth_init`
  - `unix_user_online_auth_step`
  - `change_auth_token`

Tests are passing. 
