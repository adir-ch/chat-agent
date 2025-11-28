GO ?= go

# Support cross-compilation via GOOS and GOARCH environment variables
GOOS ?= $(shell go env GOOS)
GOARCH ?= $(shell go env GOARCH)

GIT_VERSION := $(shell git describe --tags --dirty --always 2>/dev/null || echo unknown)

PROFILE_DIR := profile
SEARCH_DIR := search

# Determine binary extension based on OS
ifeq ($(GOOS),windows)
    BINARY_EXT := .exe
else
    BINARY_EXT :=
endif

PROFILE_BIN := $(PROFILE_DIR)/bin/profile$(BINARY_EXT)
SEARCH_BIN := $(SEARCH_DIR)/bin/search$(BINARY_EXT)

PROFILE_LDFLAGS := -ldflags "-X chat-agent/backend/profile/internal/version.BuildVersion=$(GIT_VERSION)"
SEARCH_LDFLAGS := -ldflags "-X chat-agent/backend/search/internal/version.BuildVersion=$(GIT_VERSION)"

# Build flags for cross-compilation
BUILD_FLAGS := GOOS=$(GOOS) GOARCH=$(GOARCH)

.PHONY: all build profile search clean test test-search test-profile init-db seed-profile

all: build

build: profile search

profile: $(PROFILE_BIN)

$(PROFILE_BIN):
	mkdir -p $(dir $@)
	$(BUILD_FLAGS) $(GO) build $(PROFILE_LDFLAGS) -o $@ ./$(PROFILE_DIR)/cmd/profile

search: $(SEARCH_BIN)

$(SEARCH_BIN):
	mkdir -p $(dir $@)
	$(BUILD_FLAGS) $(GO) build $(SEARCH_LDFLAGS) -o $@ ./$(SEARCH_DIR)/cmd/search

clean:
	make clean-profile
	make clean-search

clean-profile:
	rm -rf $(PROFILE_DIR)/bin/profile*
	rm -rf $(PROFILE_DIR)/bin/profile.exe

clean-search:
	rm -rf $(SEARCH_DIR)/bin/search*
	rm -rf $(SEARCH_DIR)/bin/search.exe

test: test-search test-profile

test-search:
	@echo "Running search service tests..."
	@bash tests/search-test.sh

test-profile:
	@echo "Running profile service tests..."
	@bash tests/profile-test.sh

init-profile-db:
	@echo "Initializing profile database..."
	@bash $(PROFILE_DIR)/scripts/init-db.sh $(dir $(PROFILE_BIN))profile.db

seed-profile: init-db

