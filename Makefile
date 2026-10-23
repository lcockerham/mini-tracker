.PHONY: lint test import-dwarven-forge link-dwarven-forge sync-minis install-sync-schedule uninstall-sync-schedule

SYNC_LABEL := com.minitracker.minisgallery-sync
SYNC_PLIST := $(HOME)/Library/LaunchAgents/$(SYNC_LABEL).plist

lint:
	ruff check .

test:
	pytest

# One-time import of the Dwarven Forge inventory CSV (pass CSV=path to override the default).
import-dwarven-forge:
	.venv/bin/python -m imports.dwarven_forge $(CSV)

# Fill empty Dwarven Forge links/pictures from imports/dwarven_forge_links.tsv.
link-dwarven-forge:
	.venv/bin/python -m imports.dwarven_forge_links

# Queue minis that are on Minis Gallery but not in the collection; review at /minis/review.
sync-minis:
	.venv/bin/python -m imports.minisgallery_sync

install-sync-schedule:
	sed -e 's|__REPO__|$(CURDIR)|g' -e 's|__HOME__|$(HOME)|g' \
		scripts/$(SYNC_LABEL).plist > $(SYNC_PLIST)
	launchctl bootout gui/$$(id -u)/$(SYNC_LABEL) 2>/dev/null || true
	launchctl bootstrap gui/$$(id -u) $(SYNC_PLIST)

uninstall-sync-schedule:
	-launchctl bootout gui/$$(id -u)/$(SYNC_LABEL)
	rm -f $(SYNC_PLIST)
