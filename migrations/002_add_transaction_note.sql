-- Migration 002: Add optional note to transactions

ALTER TABLE transactions ADD COLUMN note TEXT DEFAULT '';

