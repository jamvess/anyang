/**
 * How often the upload and reading pages ask the API again (upload-page.md §10 item 3). A page
 * constant, not a threshold of the learning model, so it is not in config/learning.yaml.
 */
export const POLL_MS = 2000;
