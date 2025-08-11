#!/bin/bash
curl -i -X POST http://127.0.0.1:8000/api/conversations/create \
  -H 'Content-Type: application/json' \
  -d '{"session_id":"smoke_123","ui_source":"web","title":"New Conversation","user_settings":{},"ui_context":{"user_id":"dev","created_from":"web_ui","browser":"curl/8"},"tags":[],"priority":"normal"}'
