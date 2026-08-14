\version "2.24.4"

\header {
  title = "Semantic Music Composition"
  composer = "AI Multi-Agent Pipeline"
  tagline = ""
}

\score {
  <<
    \new Staff \with { instrumentName = #"Violin" } {
      \clef treble
      \tempo 4 = 71
      \key g \major
      \time 4/4
      c''8\f[ e''8 a'8 fis''8 b'8 d''8 a'8 fis''8] | % Measure 1
      g'16[ b'16 d''16 b'16] g'4 b'4 d''4 | % Measure 2
      b'8[ b'8] d''4 c''8[ a'8 e''8 g'8] | % Measure 3
      c''4 a'8[ d''8 fis''8 c''8] r4 | % Measure 4
      b'8[ d''8 fis''8 d''8] b'4 d''4 | % Measure 5
      fis''8[ d''8 d''8 fis''8] e''4 c''4 | % Measure 6
      g'4 b'8[ e''8] c''4 fis''4 | % Measure 7
      a'4. e''8 c''4 r4 | % Measure 8
      fis''8[ a'8] fis''4 d''8[ fis''8] a'4 | % Measure 9
      fis''8[ fis''8 a'8 g'8 e''8 b'8 d''8 g'8] | % Measure 10
      e''8[ a'8 c''8 g'8] e''4 fis''4 | % Measure 11
      a'8[ c''8 a'8 fis''8] a'4 r4 | % Measure 12
      a'4 a'8[ c''8] b'4 g'4 | % Measure 13
      d''4. fis''8 b'4 g'4 | % Measure 14
      c''8[ e''8] b'4 g'8[ a'8] c''4 | % Measure 15
      e''8[ c''8 a'8 c''8 e''8 c''8 c''8] r8 \bar "|." % Measure 16
    }
    \new Staff \with { instrumentName = #"Cello" } {
      \clef bass
      \tempo 4 = 71
      \key g \major
      \time 4/4
      d,2\f fis,2 | % Measure 1
      b,2 d,2 | % Measure 2
      d,2 g,2 | % Measure 3
      d,2 fis,2 | % Measure 4
      b,2 d,2 | % Measure 5
      a,2 d,2 | % Measure 6
      c,2 e,2 | % Measure 7
      fis,2 a,2 | % Measure 8
      a,2 d,2 | % Measure 9
      g,2 b,2 | % Measure 10
      e,2 g,2 | % Measure 11
      a,2 d,2 | % Measure 12
      g,2 b,2 | % Measure 13
      b,2 d,2 | % Measure 14
      g,2 c,2 | % Measure 15
      c,2 e,2 \bar "|." % Measure 16
    }
  >>
  \layout { }
  \midi { }
}