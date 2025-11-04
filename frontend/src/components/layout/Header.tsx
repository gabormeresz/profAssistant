export default function Header({ title }: { title?: string }) {
  return (
    <div className="text-center mb-8">
      <h1 className="text-3xl font-bold text-gray-900 mb-2">{title}</h1>
    </div>
  );
}
