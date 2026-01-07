import aradaLogo from '../../assets/arada-logo.svg';

interface LogoProps {
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
}

export function Logo({ size = 'md' }: LogoProps) {
  const sizes = {
    sm: { height: 16 },
    md: { height: 24 },
    lg: { height: 32 },
  };

  const { height } = sizes[size];

  return (
    <div className="flex items-center">
      <img
        src={aradaLogo}
        alt="Arada"
        style={{ height: `${height}px` }}
        className="w-auto"
      />
    </div>
  );
}
