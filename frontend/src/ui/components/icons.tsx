/** Inline SVG icons: no icon font, no emoji, accessible via `aria-label`. */

import type { SVGProps } from "react";

type IconProps = SVGProps<SVGSVGElement>;

const base = (props: IconProps): IconProps => ({
  width: 20,
  height: 20,
  viewBox: "0 0 24 24",
  fill: "currentColor",
  "aria-hidden": true,
  focusable: false,
  ...props,
});

export function PlayIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M8 5v14l11-7z" />
    </svg>
  );
}

export function PauseIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M6 5h4v14H6zM14 5h4v14h-4z" />
    </svg>
  );
}

export function PreviousIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M6 6h2v12H6zM20 6v12l-9-6z" />
    </svg>
  );
}

export function NextIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M16 6h2v12h-2zM4 6l9 6-9 6z" />
    </svg>
  );
}

export function ForwardIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M12 5V2L7 6l5 4V7a6 6 0 1 1-6 6H4a8 8 0 1 0 8-8z" />
    </svg>
  );
}

export function BackIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M12 5V2l5 4-5 4V7a6 6 0 1 0 6 6h2a8 8 0 1 1-8-8z" />
    </svg>
  );
}

export function ShuffleIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M17 3l4 4-4 4V8h-2.2l-2.1 2.8L10 8H8v3l-2-2 3-3H4V3h3zM4 13l3 3H8v-3l2 2 1.3-1.7L10 12v3h2l2.7 2.8H17v-2l4 4-4 4v-3h-2.2l-2.1-2.8L10 19H8v-3l-2 2-3-3v-2z" />
    </svg>
  );
}

export function RepeatIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M7 7h10v3l4-4-4-4v3H5v6h2V7zm10 10H7v-3l-4 4 4 4v-3h12v-6h-2v4z" />
    </svg>
  );
}

export function VolumeIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M3 10v4h4l5 4V6L7 10H3zm13.5 2a4.5 4.5 0 0 0-2.5-4v8a4.5 4.5 0 0 0 2.5-4z" />
    </svg>
  );
}

export function MuteIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M3 10v4h4l5 4V6L7 10H3zm18.5 2-2.6-2.6L16.4 12l2.5 2.6 2.6-2.6z" />
    </svg>
  );
}

export function PlusIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M11 5h2v6h6v2h-6v6h-2v-6H5v-2h6z" />
    </svg>
  );
}

export function CloseIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M18.3 5.7 12 12l6.3 6.3-1.4 1.4L10.6 13.4 5.7 18.3 4.3 16.9 10.6 10.6 4.3 4.3 5.7 2.9 12 9.2l6.3-6.3z" />
    </svg>
  );
}

export function TrashIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M9 3h6l1 2h4v2H4V5h4l1-2zM6 9h12l-1 12H7L6 9z" />
    </svg>
  );
}

export function UpIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M12 6l6 6h-4v6h-4v-6H6z" />
    </svg>
  );
}

export function DownIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M12 18l-6-6h4V6h4v6h4z" />
    </svg>
  );
}

export function HeartIcon(props: IconProps): React.JSX.Element {
  return (
    <svg {...base(props)}>
      <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />
    </svg>
  );
}
