#!/bin/bash
pandoc README.md setup_savings_accounts.md setup_pension_details.md monthly_spending.md reports.md reality_report.md -o README.docx -f markdown -t docx --lua-filter=fix_links.lua


