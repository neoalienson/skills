---
name: domain-whois
description: Execute the whois command to retrieve domain registration information. Use when users request domain ownership, registration details, or DNS information for a specific domain.
metadata:
  {
    "openclaw": {
      "requires": { "anyBins": ["whois"] },
      "tags": ["whois", "domain", "dns", "lookup", "registration"]
    },
  }
---

# Domain Whois Skill

This skill executes the `whois` command to retrieve domain registration information for a given domain name.

## Purpose

Retrieve domain registration details including:
- Domain owner information
- Registration and expiration dates
- Nameservers
- Registrar information
- Contact details for the domain

## Usage

Use this skill when users request:
- Domain ownership information
- Domain registration details
- DNS information for a domain
- Domain expiration dates
- Whois lookup for a specific domain

## Security Considerations

- Validate input to prevent command injection
- Only accept domain names with standard characters (a-z, 0-9, -, .)
- Limit execution time to prevent hanging commands

## Implementation

Execute: `whois [domain_name]` with proper input sanitization.

## Examples

Input: "Who owns example.com?"
Output: Executes whois lookup for example.com and returns registration information

Input: "Get whois for google.com"
Output: Executes whois lookup for google.com and returns registration information