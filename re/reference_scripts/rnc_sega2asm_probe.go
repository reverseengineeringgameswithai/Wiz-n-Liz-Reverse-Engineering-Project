// Original research adapter. The decoder is imported from the separately pinned,
// MIT-licensed local sega2asm checkout; its source is neither copied nor patched.
package main

import (
	"bytes"
	"crypto/sha256"
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"runtime/debug"

	"sega2asm/compress"
)

const maxBytes = 1 << 20

func run() (map[string]any, error) {
	if len(os.Args) != 3 {
		return nil, fmt.Errorf("usage: rnc-sega2asm-probe bounded-input.rnc decoded-output.bin")
	}
	debug.SetMemoryLimit(64 << 20) // Soft Go limit; parent adds hard process limits.
	f, err := os.Open(os.Args[1])
	if err != nil {
		return nil, err
	}
	defer f.Close()
	src, err := io.ReadAll(io.LimitReader(f, maxBytes+19))
	if err != nil {
		return nil, err
	}
	if len(src) < 18 || len(src) > maxBytes+18 {
		return nil, fmt.Errorf("input must contain 18..%d bytes", maxBytes+18)
	}
	if !bytes.Equal(src[:4], []byte{'R', 'N', 'C', 2}) {
		return nil, fmt.Errorf("expected RNC method 2 header")
	}
	unpacked := binary.BigEndian.Uint32(src[4:8])
	packed := binary.BigEndian.Uint32(src[8:12])
	if unpacked == 0 || unpacked > maxBytes || packed == 0 || packed > maxBytes {
		return nil, fmt.Errorf("declared sizes must be 1..%d", maxBytes)
	}
	if int(packed)+18 != len(src) {
		return nil, fmt.Errorf("input must be exactly the declared block: got %d, expected %d", len(src), packed+18)
	}
	result := map[string]any{
		"declared_unpacked_size": unpacked,
		"declared_packed_size":   packed,
		"input_sha256":           fmt.Sprintf("%x", sha256.Sum256(src)),
		"decoder_error":          nil,
	}
	out, decodeErr := compress.DecompressLZHRNC2(src)
	if decodeErr != nil {
		result["decoder_error"] = decodeErr.Error()
	}
	if len(out) > maxBytes {
		return nil, fmt.Errorf("decoder returned oversized output: %d", len(out))
	}
	result["decoded_size"] = len(out)
	result["decoded_sha256"] = fmt.Sprintf("%x", sha256.Sum256(out))
	result["decoded_size_matches"] = len(out) == int(unpacked)
	if err := os.WriteFile(os.Args[2], out, 0600); err != nil {
		return nil, err
	}
	return result, nil
}

func main() {
	result, err := run()
	if err != nil {
		json.NewEncoder(os.Stdout).Encode(map[string]any{"adapter_error": err.Error()})
		os.Exit(2)
	}
	if err := json.NewEncoder(os.Stdout).Encode(result); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(2)
	}
}
